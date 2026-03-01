const agentForm = document.getElementById("agent-form");
const sessionStatus = document.getElementById("session-status");
const themeToggle = document.getElementById("theme-toggle");
const sessionUser = document.getElementById("session-user");
const logoutButton = document.getElementById("logout-button");
const questionView = document.getElementById("question-view");
const responseView = document.getElementById("response-view");
const sqlView = document.getElementById("sql-view");
const graphicView = document.getElementById("graphic-view");
const questionInput = document.getElementById("question-input");
const chatPill = document.getElementById("chat-pill");
const questionHistory = document.getElementById("question-history");
const historyMoreButton = document.getElementById("history-more");
const railTitle = document.getElementById("rail-title");
const historyTitle = document.getElementById("history-title");
const consoleTitle = document.getElementById("console-title");
const questionLabel = document.getElementById("question-label");
const responseLabel = document.getElementById("response-label");
const sqlLabel = document.getElementById("sql-label");
const dataLabel = document.getElementById("data-label");
const composerLabel = document.getElementById("composer-label");
const dataResponseButton = document.getElementById("data-response-button");
const submitButton = document.getElementById("submit-button");
const agentStatus = document.getElementById("agent-status");
const contextButtons = Array.from(document.querySelectorAll("[data-context]"));
const responseButtons = Array.from(document.querySelectorAll("[data-response-type]"));
const languageButtons = Array.from(document.querySelectorAll("[data-language]"));

const HISTORY_PAGE_SIZE = 5;
const LANGUAGE_STORAGE_KEY = "ia-agent-language";
const THEME_STORAGE_KEY = "ia-agent-theme";
const AUTH_TOKEN_STORAGE_KEY = "ia-agent-auth-token";
const AUTH_USERNAME_STORAGE_KEY = "ia-agent-auth-user";
const AUTH_EMAIL_STORAGE_KEY = "ia-agent-auth-email";
const AUTH_COOKIE_KEY = "ia_agent_auth_token";

const translations = {
  pt: {
    consoleTitle: "ANALYTICAL AGENT",
    chats: "Chats",
    previousQuestions: "Perguntas anteriores",
    showMore: "MOSTRAR MAIS {count}",
    logout: "Sair",
    theme: "TEMA",
    themeDark: "ESCURO",
    themeLight: "CLARO",
    checkingSession: "Validando sessao...",
    sessionActive: "Sessao ativa",
    sessionExpired: "Sessao expirada. Entre novamente.",
    loading: "carregando...",
    questionLabel: "PERGUNTA",
    responseLabel: "RESPOSTA",
    sqlLabel: "SQL",
    dataLabel: "DADOS",
    questionPlaceholder: "Sua pergunta aparecera aqui.",
    responsePlaceholder: "A resposta em linguagem natural aparecera aqui.",
    sqlPlaceholder: "O SQL gerado aparecera aqui.",
    dataPlaceholder: "Os dados salvos aparecerao aqui.",
    composerLabel: "FACA SUA PERGUNTA AQUI",
    inputPlaceholder: "Digite sua pergunta...",
    send: "ENVIAR",
    historyEmpty: "Suas perguntas anteriores ficarao aqui.",
    unableLoadSavedData: "Nao foi possivel carregar os dados salvos.",
    loadingSavedData: "Carregando dados salvos...",
    noNaturalResponse: "Nenhuma resposta em linguagem natural.",
    noSql: "Nenhum SQL retornado.",
    noRows: "Nenhum dado retornado.",
    unableLoadChatHistory: "Nao foi possivel carregar o historico do chat.",
    questionRequired: "A pergunta e obrigatoria.",
    processingRequest: "Processando solicitacao...",
    generatingSql: "Gerando SQL...",
    waitingSavedData: "Aguardando dados salvos...",
    callingAgent: "Chamando o agente...",
    responseReceived: "Resposta recebida.",
    sqlUnavailable: "SQL indisponivel porque a solicitacao falhou.",
    noDataAvailable: "Nenhum dado disponivel.",
    openQuestion: "Abrir pergunta",
    requestFailed: "Falha na solicitacao.",
  },
  en: {
    consoleTitle: "ANALYTICAL AGENT",
    chats: "Chats",
    previousQuestions: "Previous questions",
    showMore: "SHOW {count} MORE",
    logout: "Logout",
    theme: "THEME",
    themeDark: "DARK",
    themeLight: "LIGHT",
    checkingSession: "Validating session...",
    sessionActive: "Session active",
    sessionExpired: "Session expired. Login again.",
    loading: "loading...",
    questionLabel: "QUESTION",
    responseLabel: "RESPONSE",
    sqlLabel: "SQL",
    dataLabel: "DATA",
    questionPlaceholder: "Your question will appear here.",
    responsePlaceholder: "The natural language response will appear here.",
    sqlPlaceholder: "Generated SQL will appear here.",
    dataPlaceholder: "Saved data will appear here.",
    composerLabel: "ASK YOUR QUESTION HERE",
    inputPlaceholder: "Type your question...",
    send: "SEND",
    historyEmpty: "Your previous questions will stay here.",
    unableLoadSavedData: "Unable to load saved data.",
    loadingSavedData: "Loading saved data...",
    noNaturalResponse: "No natural language response.",
    noSql: "No SQL returned.",
    noRows: "No data returned.",
    unableLoadChatHistory: "Unable to load chat history.",
    questionRequired: "Question is required.",
    processingRequest: "Processing request...",
    generatingSql: "Generating SQL...",
    waitingSavedData: "Waiting for saved data...",
    callingAgent: "Calling the agent...",
    responseReceived: "Response received.",
    sqlUnavailable: "SQL unavailable because the request failed.",
    noDataAvailable: "No data available.",
    openQuestion: "Open question",
    requestFailed: "Request failed.",
  },
  es: {
    consoleTitle: "ANALYTICAL AGENT",
    chats: "Chats",
    previousQuestions: "Preguntas anteriores",
    showMore: "MOSTRAR {count} MAS",
    logout: "Salir",
    theme: "TEMA",
    themeDark: "OSCURO",
    themeLight: "CLARO",
    checkingSession: "Validando sesion...",
    sessionActive: "Sesion activa",
    sessionExpired: "Sesion expirada. Inicia sesion otra vez.",
    loading: "cargando...",
    questionLabel: "PREGUNTA",
    responseLabel: "RESPUESTA",
    sqlLabel: "SQL",
    dataLabel: "DATOS",
    questionPlaceholder: "Tu pregunta aparecera aqui.",
    responsePlaceholder: "La respuesta en lenguaje natural aparecera aqui.",
    sqlPlaceholder: "El SQL generado aparecera aqui.",
    dataPlaceholder: "Los datos guardados apareceran aqui.",
    composerLabel: "HAZ TU PREGUNTA AQUI",
    inputPlaceholder: "Escribe tu pregunta...",
    send: "ENVIAR",
    historyEmpty: "Tus preguntas anteriores se quedaran aqui.",
    unableLoadSavedData: "No se pudieron cargar los datos guardados.",
    loadingSavedData: "Cargando datos guardados...",
    noNaturalResponse: "No hay respuesta en lenguaje natural.",
    noSql: "No se devolvio SQL.",
    noRows: "No se devolvieron datos.",
    unableLoadChatHistory: "No se pudo cargar el historial del chat.",
    questionRequired: "La pregunta es obligatoria.",
    processingRequest: "Procesando solicitud...",
    generatingSql: "Generando SQL...",
    waitingSavedData: "Esperando datos guardados...",
    callingAgent: "Llamando al agente...",
    responseReceived: "Respuesta recibida.",
    sqlUnavailable: "SQL no disponible porque la solicitud fallo.",
    noDataAvailable: "No hay datos disponibles.",
    openQuestion: "Abrir pregunta",
    requestFailed: "La solicitud fallo.",
  },
};

let authToken = "";
let authenticatedUsername = "";
let authenticatedEmail = "";
let currentTheme = "dark";
let currentLanguage = "pt";
let messageHistory = [];
let visibleHistoryCount = HISTORY_PAGE_SIZE;
let selectedMessageId = "";

function t(key) {
  return translations[currentLanguage]?.[key] || translations.pt[key] || key;
}

function setStatus(element, message, type = "") {
  element.textContent = message;
  element.className = element.id === "session-status"
    ? `status-chip ${type}`.trim()
    : `status-line ${type}`.trim();
}

function activateButton(buttons, activeButton) {
  buttons.forEach((button) => {
    button.classList.toggle("active", button === activeButton);
  });
}

function setPlaceholder(element, message) {
  element.textContent = message;
  element.classList.add("box-placeholder");
}

function setBoxContent(element, message) {
  element.textContent = message;
  element.classList.toggle("box-placeholder", !message);
}

function setBoxLabel(element, key) {
  element.textContent = `<${t(key)}>`;
}

function refreshPlaceholder(element, key) {
  if (!element.classList.contains("box-placeholder")) {
    return;
  }

  setPlaceholder(element, t(key));
}

function renderThemeLabel() {
  const themeState = currentTheme === "light" ? t("themeLight") : t("themeDark");
  themeToggle.textContent = `${t("theme")}: ${themeState}`;
}

function renderSessionUi(statusMessage = t("checkingSession"), statusType = "") {
  sessionUser.textContent = authenticatedEmail || authenticatedUsername || "-";
  setStatus(sessionStatus, statusMessage, statusType);
}

function updateStaticText() {
  document.documentElement.lang = currentLanguage;
  railTitle.textContent = t("chats");
  historyTitle.textContent = t("previousQuestions");
  historyMoreButton.textContent = t("showMore").replace("{count}", String(HISTORY_PAGE_SIZE));
  consoleTitle.textContent = t("consoleTitle");
  logoutButton.textContent = t("logout");
  setBoxLabel(questionLabel, "questionLabel");
  setBoxLabel(responseLabel, "responseLabel");
  setBoxLabel(sqlLabel, "sqlLabel");
  setBoxLabel(dataLabel, "dataLabel");
  composerLabel.textContent = t("composerLabel");
  questionInput.placeholder = t("inputPlaceholder");
  dataResponseButton.textContent = t("dataLabel");
  submitButton.textContent = t("send");

  if (!chatPill.dataset.chatId) {
    chatPill.textContent = t("loading");
  }

  refreshPlaceholder(questionView, "questionPlaceholder");
  refreshPlaceholder(responseView, "responsePlaceholder");
  refreshPlaceholder(sqlView, "sqlPlaceholder");
  refreshPlaceholder(graphicView, "dataPlaceholder");
  renderSessionUi(authToken ? t("sessionActive") : t("checkingSession"), authToken ? "success" : "");
  renderThemeLabel();
  renderMessageHistory();
}

function applyLanguage(language) {
  currentLanguage = translations[language] ? language : "pt";
  const activeButton = languageButtons.find(
    (button) => button.dataset.language === currentLanguage
  );
  activateButton(languageButtons, activeButton);
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, currentLanguage);
  updateStaticText();
}

function loadLanguagePreference() {
  const savedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  applyLanguage(savedLanguage || "pt");
}

function applyTheme(theme) {
  currentTheme = theme === "light" ? "light" : "dark";
  document.body.classList.toggle("light-theme", currentTheme === "light");
  renderThemeLabel();
}

function loadThemePreference() {
  const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  applyTheme(savedTheme || "dark");
}

function setAuthCookie(token) {
  document.cookie = `${AUTH_COOKIE_KEY}=${encodeURIComponent(token)}; path=/; SameSite=Lax`;
}

function clearAuthCookie() {
  document.cookie = `${AUTH_COOKIE_KEY}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
}

function persistSession(payload, token) {
  authToken = token;
  authenticatedUsername = payload.username || "";
  authenticatedEmail = payload.email || "";

  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, authToken);
  window.localStorage.setItem(AUTH_USERNAME_STORAGE_KEY, authenticatedUsername);
  window.localStorage.setItem(AUTH_EMAIL_STORAGE_KEY, authenticatedEmail);
  setAuthCookie(authToken);

  agentForm.elements.namedItem("email").value = authenticatedEmail;
  renderSessionUi(t("sessionActive"), "success");
}

function clearStoredSession() {
  authToken = "";
  authenticatedUsername = "";
  authenticatedEmail = "";

  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_USERNAME_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY);
  clearAuthCookie();

  agentForm.elements.namedItem("email").value = "";
}

function loadStoredSession() {
  authToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) || "";
  authenticatedUsername = window.localStorage.getItem(AUTH_USERNAME_STORAGE_KEY) || "";
  authenticatedEmail = window.localStorage.getItem(AUTH_EMAIL_STORAGE_KEY) || "";
  agentForm.elements.namedItem("email").value = authenticatedEmail;
}

function redirectToLogin() {
  clearStoredSession();
  window.location.replace("/login");
}

async function validateSessionOrRedirect() {
  loadStoredSession();

  if (!authToken) {
    redirectToLogin();
    return null;
  }

  renderSessionUi(t("checkingSession"));

  try {
    const response = await fetch("/v1/session", {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(t("sessionExpired"));
    }

    const payload = await response.json();
    persistSession(payload, authToken);
    return payload;
  } catch {
    redirectToLogin();
    return null;
  }
}

function generateHash(length = 32) {
  if (window.crypto && typeof window.crypto.getRandomValues === "function") {
    const bytes = new Uint8Array(Math.max(2, Math.floor(length / 2)));
    window.crypto.getRandomValues(bytes);
    return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  const fallback = `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`;
  return fallback.padEnd(length, "0").slice(0, length);
}

function syncChatId(chatId) {
  const normalizedChatId = String(chatId || "").trim() || generateHash();
  agentForm.elements.namedItem("chat_id").value = normalizedChatId;
  chatPill.dataset.chatId = normalizedChatId;
  chatPill.textContent = normalizedChatId;
}

function normalizeMessage(entry) {
  if (!entry || typeof entry !== "object") {
    return null;
  }

  const question = String(entry.question || "").trim();
  if (!question) {
    return null;
  }

  return {
    mensage_id: String(entry.mensage_id || generateHash()).trim() || generateHash(),
    question,
    response: String(entry.response || ""),
    query: String(entry.query || ""),
    data_path: String(entry.data_path || ""),
    created_at: String(entry.created_at || ""),
  };
}

async function loadMessageRows(dataPath) {
  if (!dataPath) {
    return [];
  }

  const response = await fetch(dataPath, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(t("unableLoadSavedData"));
  }

  const payload = await response.json();
  return Array.isArray(payload) ? payload : [];
}

async function showMessageDetails(messageId) {
  const entry = messageHistory.find((item) => item.mensage_id === messageId);
  if (!entry) {
    return;
  }

  selectedMessageId = messageId;
  renderMessageHistory();

  setBoxContent(questionView, entry.question);
  setBoxContent(responseView, entry.response || t("noNaturalResponse"));
  setBoxContent(sqlView, entry.query || t("noSql"));

  if (!entry.data_path) {
    setBoxContent(graphicView, t("noRows"));
    return;
  }

  const requestedMessageId = messageId;
  setBoxContent(graphicView, t("loadingSavedData"));

  try {
    const rows = await loadMessageRows(entry.data_path);
    if (selectedMessageId !== requestedMessageId) {
      return;
    }

    setBoxContent(
      graphicView,
      rows.length ? JSON.stringify(rows, null, 2) : t("noRows")
    );
  } catch (error) {
    if (selectedMessageId !== requestedMessageId) {
      return;
    }

    setBoxContent(graphicView, error.message || t("unableLoadSavedData"));
  }
}

function getSortedMessageHistory() {
  return messageHistory
    .map((entry, index) => ({ ...entry, sortIndex: index }))
    .sort((left, right) => {
      const leftTime = Date.parse(left.created_at);
      const rightTime = Date.parse(right.created_at);

      if (!Number.isNaN(leftTime) && !Number.isNaN(rightTime) && leftTime !== rightTime) {
        return rightTime - leftTime;
      }

      if (!Number.isNaN(rightTime)) {
        return 1;
      }

      if (!Number.isNaN(leftTime)) {
        return -1;
      }

      return right.sortIndex - left.sortIndex;
    });
}

function renderMessageHistory() {
  questionHistory.replaceChildren();
  const sortedHistory = getSortedMessageHistory();
  const visibleHistory = sortedHistory.slice(0, visibleHistoryCount);
  const hasMoreHistory = sortedHistory.length > visibleHistoryCount;

  historyMoreButton.hidden = !hasMoreHistory;
  historyMoreButton.disabled = !hasMoreHistory;
  historyMoreButton.textContent = t("showMore").replace("{count}", String(HISTORY_PAGE_SIZE));

  if (!sortedHistory.length) {
    const emptyState = document.createElement("p");
    emptyState.className = "question-history-empty";
    emptyState.textContent = t("historyEmpty");
    questionHistory.append(emptyState);
    return;
  }

  const fragment = document.createDocumentFragment();

  visibleHistory.forEach((entry) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "history-item";
    card.dataset.messageId = entry.mensage_id;
    card.classList.toggle("active", entry.mensage_id === selectedMessageId);
    card.title = entry.mensage_id;
    card.setAttribute("aria-label", `${t("openQuestion")} ${entry.mensage_id}`);

    const text = document.createElement("p");
    text.className = "history-question";
    text.textContent = entry.question;

    card.append(text);
    fragment.append(card);
  });

  questionHistory.append(fragment);
  questionHistory.scrollTop = 0;
}

function addMessageToHistory(entry) {
  const normalizedEntry = normalizeMessage(entry);
  if (!normalizedEntry) {
    return;
  }

  selectedMessageId = normalizedEntry.mensage_id;
  messageHistory = [...messageHistory, normalizedEntry];
  renderMessageHistory();
}

async function loadMockMessages() {
  try {
    const response = await fetch("/chat_mensages.json", {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(t("unableLoadChatHistory"));
    }

    const payload = await response.json();
    syncChatId(payload.chat_id);
    visibleHistoryCount = HISTORY_PAGE_SIZE;
    selectedMessageId = "";
    messageHistory = Array.isArray(payload.mensages)
      ? payload.mensages.map((entry) => normalizeMessage(entry)).filter(Boolean)
      : [];
    renderMessageHistory();
  } catch (error) {
    chatPill.dataset.chatId = "";
    chatPill.textContent = t("loading");
    visibleHistoryCount = HISTORY_PAGE_SIZE;
    selectedMessageId = "";
    messageHistory = [];
    renderMessageHistory();
    setStatus(sessionStatus, error.message, "error");
  }
}

async function initializeApp() {
  const session = await validateSessionOrRedirect();
  if (!session) {
    return;
  }

  await loadMockMessages();
}

loadLanguagePreference();
loadThemePreference();
initializeApp();

themeToggle.addEventListener("click", () => {
  const nextTheme = currentTheme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
  window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
});

languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applyLanguage(button.dataset.language);
  });
});

logoutButton.addEventListener("click", () => {
  redirectToLogin();
});

historyMoreButton.addEventListener("click", () => {
  visibleHistoryCount += HISTORY_PAGE_SIZE;
  renderMessageHistory();
});

questionInput.addEventListener("keydown", (event) => {
  if (
    event.key !== "Enter" ||
    event.shiftKey ||
    event.ctrlKey ||
    event.altKey ||
    event.metaKey ||
    event.isComposing
  ) {
    return;
  }

  event.preventDefault();
  agentForm.requestSubmit();
});

questionHistory.addEventListener("click", (event) => {
  const card = event.target.closest(".history-item");
  if (!card) {
    return;
  }

  showMessageDetails(card.dataset.messageId);
});

contextButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activateButton(contextButtons, button);
    const value = button.dataset.context;
    agentForm.elements.namedItem("question_context").value =
      value === "CS" || value === "OTHERS" ? "" : value;
  });
});

responseButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activateButton(responseButtons, button);
    const value = button.dataset.responseType;
    agentForm.elements.namedItem("response_type").value = value;
  });
});

agentForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const session = await validateSessionOrRedirect();
  if (!session) {
    return;
  }

  const formData = new FormData(agentForm);
  const question = String(formData.get("question") || "").trim();

  if (!question) {
    setStatus(agentStatus, t("questionRequired"), "error");
    return;
  }

  const chatId = String(formData.get("chat_id") || "").trim() || generateHash();
  const messageId = generateHash();
  syncChatId(chatId);
  agentForm.elements.namedItem("question_id").value = messageId;
  agentForm.elements.namedItem("email").value = authenticatedEmail;

  addMessageToHistory({
    mensage_id: messageId,
    question,
    response: "",
    query: "",
    data_path: "",
    created_at: new Date().toISOString(),
  });

  setBoxContent(questionView, question);
  setBoxContent(responseView, t("processingRequest"));
  setBoxContent(sqlView, t("generatingSql"));
  setBoxContent(graphicView, t("waitingSavedData"));
  setStatus(agentStatus, t("callingAgent"));

  const body = {
    email: authenticatedEmail,
    chat_id: chatId,
    question_id: messageId,
    response_type: formData.get("response_type") || null,
    question_context: formData.get("question_context") || null,
    question,
  };

  try {
    const response = await fetch("/v1/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify(body),
    });

    let payload = {};
    try {
      payload = await response.json();
    } catch {
      payload = {};
    }

    if (response.status === 401) {
      redirectToLogin();
      return;
    }

    if (!response.ok) {
      throw new Error(payload.detail || t("requestFailed"));
    }

    const result = payload.response || {};
    const rows = Array.isArray(result.response_data) ? result.response_data : [];

    setBoxContent(
      responseView,
      result.response_natural_language || t("noNaturalResponse")
    );
    setBoxContent(sqlView, result.response_sql || t("noSql"));
    setBoxContent(
      graphicView,
      rows.length ? JSON.stringify(rows, null, 2) : t("noRows")
    );

    messageHistory = messageHistory.map((entry) => (
      entry.mensage_id === messageId
        ? {
            ...entry,
            response: String(result.response_natural_language || ""),
            query: String(result.response_sql || ""),
            data_path: String(result.data_path || ""),
          }
        : entry
    ));

    renderMessageHistory();
    setStatus(agentStatus, t("responseReceived"), "success");
    setStatus(sessionStatus, t("sessionActive"), "success");
    questionInput.value = "";
  } catch (error) {
    setBoxContent(responseView, error.message);
    setPlaceholder(sqlView, t("sqlUnavailable"));
    setPlaceholder(graphicView, t("noDataAvailable"));
    setStatus(agentStatus, error.message, "error");
  }
});
