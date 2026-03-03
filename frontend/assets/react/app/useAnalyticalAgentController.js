import { useEffect, useState } from "../shared/cdn.js";
import {
  applyTheme,
  loadLanguagePreference,
  loadStoredSession,
  loadThemePreference,
  saveLanguagePreference,
  saveThemePreference,
} from "../shared/browserStore.js";
import {
  CONTEXT_OPTIONS,
  DEFAULT_RESPONSE_TYPES,
  HISTORY_PAGE_SIZE,
  RESPONSE_OPTIONS,
  RUNTIME_LOG_PAGE_SIZE,
} from "../shared/constants.js";
import { createHashId } from "../shared/utils.js";
import { createAppTranslator } from "./translations.js";
import {
  askAgentRequest,
  loadChatHistoryRequest,
  loadMessageRowsRequest,
  loadRuntimeLogsRequest,
  requestGraphRequest,
  resolveApiError,
  validateSessionRequest,
} from "./api.js";
import {
  createPendingMessage,
  normalizeMessage,
  patchMessageCollection,
  sortMessageCollection,
} from "./messageService.js";
import { redirectToLogin } from "./navigation.js";

function resolveQuestionContextValue(selectedContextId) {
  return CONTEXT_OPTIONS.find((option) => option.id === selectedContextId)?.value || null;
}

function normalizeResponseTypes(responseTypes, fallbackValues) {
  return Array.isArray(responseTypes) && responseTypes.length
    ? responseTypes
      .map((value) => String(value || "").trim().toUpperCase())
      .filter(Boolean)
    : fallbackValues;
}

export function useAnalyticalAgentController() {
  const [storedSession] = useState(() => loadStoredSession());
  const [language, setLanguage] = useState(loadLanguagePreference());
  const [theme, setTheme] = useState(loadThemePreference());
  const [authToken, setAuthToken] = useState(storedSession.token);
  const [email, setEmail] = useState(storedSession.email || "-");
  const [canViewRuntimeLogs, setCanViewRuntimeLogs] = useState(
    storedSession.canViewRuntimeLogs,
  );
  const [sessionStatus, setSessionStatus] = useState({
    message: "",
    type: "",
  });
  const [chatId, setChatId] = useState("");
  const [messages, setMessages] = useState([]);
  const [selectedMessageId, setSelectedMessageId] = useState("");
  const [visibleHistoryCount, setVisibleHistoryCount] = useState(HISTORY_PAGE_SIZE);
  const [question, setQuestion] = useState("");
  const [questionContext, setQuestionContext] = useState("TRAVEL");
  const [responseTypes, setResponseTypes] = useState([...DEFAULT_RESPONSE_TYPES]);
  const [agentStatus, setAgentStatus] = useState({
    message: "",
    type: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [graphBusyId, setGraphBusyId] = useState("");
  const [runtimeState, setRuntimeState] = useState({
    logs: "",
    status: "",
    lineCount: RUNTIME_LOG_PAGE_SIZE,
    loading: false,
  });

  const t = createAppTranslator(language);

  useEffect(() => {
    document.documentElement.lang = language;
    saveLanguagePreference(language);
  }, [language]);

  useEffect(() => {
    const normalizedTheme = applyTheme(theme);
    if (normalizedTheme !== theme) {
      setTheme(normalizedTheme);
      return;
    }

    saveThemePreference(normalizedTheme);
  }, [theme]);

  async function refreshRuntimeLogs({
    token = authToken,
    lineCount = runtimeState.lineCount,
    overrideMessage = t("runtimeLoading"),
    onCancel = null,
  } = {}) {
    if (!token) {
      return;
    }

    setRuntimeState((currentState) => ({
      ...currentState,
      loading: true,
      lineCount,
      status: overrideMessage,
    }));

    const { response, payload } = await loadRuntimeLogsRequest(token, lineCount);
    if (onCancel && onCancel()) {
      return;
    }

    if (response.status === 401) {
      redirectToLogin();
      return;
    }

    if (!response.ok) {
      setRuntimeState((currentState) => ({
        ...currentState,
        loading: false,
        status: t("runtimeError"),
      }));
      return;
    }

    if (!payload?.can_view_runtime_logs) {
      setCanViewRuntimeLogs(false);
      setRuntimeState((currentState) => ({
        ...currentState,
        logs: "",
        loading: false,
        status: t("runtimeHidden"),
      }));
      return;
    }

    const logs = String(payload.logs || "");
    setRuntimeState((currentState) => ({
      ...currentState,
      logs,
      loading: false,
      status: logs ? "" : t("runtimeEmpty"),
    }));
  }

  useEffect(() => {
    let isCancelled = false;

    async function bootstrap() {
      if (!storedSession.token) {
        redirectToLogin();
        return;
      }

      setSessionStatus({
        message: t("checkingSession"),
        type: "",
      });
      setRuntimeState((currentState) => ({
        ...currentState,
        status: t("runtimeWaiting"),
      }));

      const { response, payload } = await validateSessionRequest(storedSession.token);
      if (isCancelled) {
        return;
      }

      if (!response.ok) {
        redirectToLogin();
        return;
      }

      const resolvedEmail = String(payload?.email || storedSession.email || "-");
      const runtimePermission = Boolean(payload?.can_view_runtime_logs);

      setAuthToken(storedSession.token);
      setEmail(resolvedEmail);
      setCanViewRuntimeLogs(runtimePermission);
      setSessionStatus({
        message: t("sessionActive"),
        type: "success",
      });

      const chatHistoryResult = await loadChatHistoryRequest();
      if (isCancelled) {
        return;
      }

      if (!chatHistoryResult.response.ok) {
        setChatId("");
        setMessages([]);
        setSelectedMessageId("");
        setSessionStatus({
          message: t("unableLoadChatHistory"),
          type: "error",
        });
      } else {
        const nextChatId = String(chatHistoryResult.payload?.chat_id || "").trim()
          || createHashId();
        const nextMessages = Array.isArray(chatHistoryResult.payload?.mensages)
          ? chatHistoryResult.payload.mensages
            .map((entry) => normalizeMessage(entry))
            .filter(Boolean)
          : [];

        setChatId(nextChatId);
        setMessages(nextMessages);
        setSelectedMessageId("");
        setVisibleHistoryCount(HISTORY_PAGE_SIZE);
      }

      if (!runtimePermission) {
        setRuntimeState((currentState) => ({
          ...currentState,
          logs: "",
          status: t("runtimeHidden"),
          loading: false,
        }));
        return;
      }

      await refreshRuntimeLogs({
        token: storedSession.token,
        lineCount: RUNTIME_LOG_PAGE_SIZE,
        overrideMessage: t("runtimeLoading"),
        onCancel: () => isCancelled,
      });
    }

    bootstrap();

    return () => {
      isCancelled = true;
    };
  }, []);

  function toggleTheme() {
    setTheme((currentTheme) => (currentTheme === "light" ? "dark" : "light"));
  }

  function logout() {
    redirectToLogin();
  }

  function selectContext(optionId) {
    setQuestionContext(optionId);
  }

  function toggleResponseType(nextType) {
    setResponseTypes((currentTypes) => {
      const nextSelection = new Set(currentTypes);

      if (nextSelection.has(nextType)) {
        if (nextSelection.size === 1) {
          return currentTypes;
        }

        nextSelection.delete(nextType);
      } else {
        nextSelection.add(nextType);
      }

      return RESPONSE_OPTIONS.filter((option) => nextSelection.has(option));
    });
  }

  async function selectMessage(messageId) {
    setSelectedMessageId(messageId);

    const targetMessage = messages.find((entry) => entry.mensage_id === messageId);
    if (
      !targetMessage
      || !targetMessage.data_path
      || Array.isArray(targetMessage.data_rows)
      || targetMessage.data_loading
    ) {
      return;
    }

    setMessages((currentMessages) => patchMessageCollection(currentMessages, messageId, {
      data_loading: true,
      data_error: "",
    }));

    try {
      const rows = await loadMessageRowsRequest(
        targetMessage.data_path,
        t("unableLoadSavedData"),
      );

      setMessages((currentMessages) => patchMessageCollection(currentMessages, messageId, {
        data_rows: rows,
        data_loading: false,
        data_error: "",
      }));
    } catch (error) {
      setMessages((currentMessages) => patchMessageCollection(currentMessages, messageId, {
        data_rows: [],
        data_loading: false,
        data_error: error.message || t("unableLoadSavedData"),
      }));
    }
  }

  async function submitQuestion(event) {
    event.preventDefault();

    if (!authToken) {
      redirectToLogin();
      return;
    }

    const cleanQuestion = question.trim();
    if (!cleanQuestion) {
      setAgentStatus({
        message: t("questionRequired"),
        type: "error",
      });
      return;
    }

    const nextChatId = chatId || createHashId();
    const messageId = createHashId();
    const pendingMessage = createPendingMessage({
      messageId,
      question: cleanQuestion,
      responseTypes,
    });

    setChatId(nextChatId);
    setSelectedMessageId(messageId);
    setMessages((currentMessages) => [...currentMessages, pendingMessage]);
    setAgentStatus({
      message: t("callingAgent"),
      type: "",
    });
    setQuestion("");
    setIsSubmitting(true);

    try {
      const { response, payload } = await askAgentRequest(authToken, {
        email,
        chat_id: nextChatId,
        question_id: messageId,
        response_types: responseTypes,
        question_context: resolveQuestionContextValue(questionContext),
        question: cleanQuestion,
      });

      if (response.status === 401) {
        redirectToLogin();
        return;
      }

      if (!response.ok) {
        throw new Error(resolveApiError(payload, t("requestFailed")));
      }

      const result = payload?.response && typeof payload.response === "object"
        ? payload.response
        : {};

      setMessages((currentMessages) => patchMessageCollection(currentMessages, messageId, {
        response: String(result.response_natural_language || ""),
        query: String(result.response_sql || ""),
        data_path: String(result.data_path || ""),
        graph_path: String(result.graph_path || ""),
        selected_graph_pattern: String(result.selected_graph_pattern || ""),
        response_types: normalizeResponseTypes(result.response_types, responseTypes),
        graph_suggestions: Array.isArray(result.graph_suggestions)
          ? result.graph_suggestions
          : [],
        data_rows: Array.isArray(result.response_data) ? result.response_data : [],
        data_loading: false,
        data_error: "",
        graph_error: "",
        is_pending: false,
      }));

      setAgentStatus({
        message: t("responseReceived"),
        type: "success",
      });
      setSessionStatus({
        message: t("sessionActive"),
        type: "success",
      });

      if (canViewRuntimeLogs) {
        await refreshRuntimeLogs();
      }
    } catch (error) {
      setMessages((currentMessages) => patchMessageCollection(currentMessages, messageId, {
        response: String(error.message || t("requestFailed")),
        query: "",
        data_path: "",
        graph_path: "",
        selected_graph_pattern: "",
        graph_suggestions: [],
        data_rows: [],
        data_loading: false,
        data_error: "",
        graph_error: "",
        is_pending: false,
      }));

      setAgentStatus({
        message: error.message || t("requestFailed"),
        type: "error",
      });

      if (canViewRuntimeLogs) {
        await refreshRuntimeLogs();
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function requestGraph(graphPatternId) {
    if (!selectedMessageId || !authToken) {
      return;
    }

    setGraphBusyId(selectedMessageId);
    setMessages((currentMessages) => patchMessageCollection(currentMessages, selectedMessageId, {
      graph_error: "",
    }));

    try {
      const { response, payload } = await requestGraphRequest(authToken, {
        chat_id: chatId,
        question_id: selectedMessageId,
        graph_pattern_id: graphPatternId,
      });

      if (response.status === 401) {
        redirectToLogin();
        return;
      }

      if (!response.ok) {
        throw new Error(resolveApiError(payload, t("graphFailed")));
      }

      setMessages((currentMessages) => patchMessageCollection(currentMessages, selectedMessageId, {
        graph_path: String(payload?.graph_path || ""),
        selected_graph_pattern: String(payload?.selected_graph_pattern || ""),
        graph_suggestions: Array.isArray(payload?.graph_suggestions)
          ? payload.graph_suggestions
          : [],
        graph_error: "",
      }));

      if (canViewRuntimeLogs) {
        await refreshRuntimeLogs();
      }
    } catch (error) {
      setMessages((currentMessages) => patchMessageCollection(currentMessages, selectedMessageId, {
        graph_error: error.message || t("graphFailed"),
      }));

      if (canViewRuntimeLogs) {
        await refreshRuntimeLogs();
      }
    } finally {
      setGraphBusyId("");
    }
  }

  function showMoreHistory() {
    setVisibleHistoryCount((count) => count + HISTORY_PAGE_SIZE);
  }

  async function showMoreRuntimeLogs() {
    await refreshRuntimeLogs({
      lineCount: runtimeState.lineCount + RUNTIME_LOG_PAGE_SIZE,
    });
  }

  const sortedMessages = sortMessageCollection(messages);

  return {
    t,
    language,
    setLanguage,
    theme,
    toggleTheme,
    email,
    sessionStatus,
    canViewRuntimeLogs,
    chatId,
    visibleMessages: sortedMessages.slice(0, visibleHistoryCount),
    hasMoreHistory: sortedMessages.length > visibleHistoryCount,
    showMoreHistory,
    selectedMessageId,
    selectedMessage: messages.find((entry) => entry.mensage_id === selectedMessageId) || null,
    question,
    setQuestion,
    questionContext,
    selectContext,
    responseTypes,
    toggleResponseType,
    agentStatus,
    isSubmitting,
    submitQuestion,
    graphBusyId,
    requestGraph,
    runtimeState,
    showMoreRuntimeLogs,
    logout,
    selectMessage,
  };
}
