const agentForm = document.getElementById("agent-form");
const sessionStatus = document.getElementById("session-status");
const themeToggle = document.getElementById("theme-toggle");
const sessionUser = document.getElementById("session-user");
const logoutButton = document.getElementById("logout-button");
const questionView = document.getElementById("question-view");
const responseView = document.getElementById("response-view");
const sqlView = document.getElementById("sql-view");
const dataView = document.getElementById("data-view");
const graphView = document.getElementById("graph-view");
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
const graphLabel = document.getElementById("graph-label");
const runtimePanel = document.getElementById("runtime-panel");
const runtimeTitle = document.getElementById("runtime-title");
const runtimeStatus = document.getElementById("runtime-status");
const runtimeMoreButton = document.getElementById("runtime-more");
const runtimeLogView = document.getElementById("runtime-log-view");
const composerLabel = document.getElementById("composer-label");
const graphSuggestionsView = document.getElementById("graph-suggestions");
const graphDownloadLink = document.getElementById("graph-download");
const graphStatus = document.getElementById("graph-status");
const dataResponseButton = document.getElementById("data-response-button");
const submitButton = document.getElementById("submit-button");
const agentStatus = document.getElementById("agent-status");
const workspaceShell = document.querySelector(".workspace-shell");
const contextButtons = Array.from(document.querySelectorAll("[data-context]"));
const responseButtons = Array.from(document.querySelectorAll("[data-response-type]"));
const languageButtons = Array.from(document.querySelectorAll("[data-language]"));

const HISTORY_PAGE_SIZE = 5;
const RUNTIME_LOG_PAGE_SIZE = 60;
const LANGUAGE_STORAGE_KEY = "ia-agent-language";
const THEME_STORAGE_KEY = "ia-agent-theme";
const AUTH_TOKEN_STORAGE_KEY = "ia-agent-auth-token";
const AUTH_EMAIL_STORAGE_KEY = "ia-agent-auth-email";
const AUTH_LOG_PERMISSION_STORAGE_KEY = "ia-agent-log-permission";
const AUTH_COOKIE_KEY = "ia_agent_auth_token";
const DEFAULT_RESPONSE_TYPES = ["TEXT", "SQL"];

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
    graphLabel: "GRAFICO",
    questionPlaceholder: "Sua pergunta aparecera aqui.",
    responsePlaceholder: "A resposta em linguagem natural aparecera aqui.",
    sqlPlaceholder: "O SQL gerado aparecera aqui.",
    dataPlaceholder: "Os dados salvos aparecerao aqui.",
    graphPlaceholder: "O grafico gerado aparecera aqui.",
    runtimeTitle: "Logs em tempo real",
    runtimeWaiting: "Aguardando sessao...",
    runtimeHidden: "Voce nao tem acesso aos logs em tempo real.",
    runtimeLoading: "Carregando logs...",
    runtimeEmpty: "Nenhum log disponivel ainda.",
    runtimeError: "Nao foi possivel carregar os logs.",
    runtimeShowMore: "MOSTRAR MAIS LOGS",
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
    textDisabled: "Saida TEXT desativada para esta solicitacao.",
    sqlDisabled: "Saida SQL desativada para esta solicitacao.",
    graphDisabled: "Saida GRAPH desativada para esta solicitacao.",
    graphMode: "GRAPH",
    noGraphSuggestions: "Nenhum grafico sugerido para estes dados.",
    generatingGraph: "Gerando grafico...",
    graphReady: "Grafico pronto.",
    graphFailed: "Nao foi possivel gerar o grafico.",
    downloadGraph: "BAIXAR GRAFICO",
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
    graphLabel: "GRAPH",
    questionPlaceholder: "Your question will appear here.",
    responsePlaceholder: "The natural language response will appear here.",
    sqlPlaceholder: "Generated SQL will appear here.",
    dataPlaceholder: "Saved data will appear here.",
    graphPlaceholder: "The generated graph will appear here.",
    runtimeTitle: "Runtime logs",
    runtimeWaiting: "Waiting for session...",
    runtimeHidden: "You do not have access to runtime logs.",
    runtimeLoading: "Loading logs...",
    runtimeEmpty: "No logs available yet.",
    runtimeError: "Unable to load runtime logs.",
    runtimeShowMore: "SHOW MORE LOGS",
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
    textDisabled: "TEXT output disabled for this request.",
    sqlDisabled: "SQL output disabled for this request.",
    graphDisabled: "GRAPH output disabled for this request.",
    graphMode: "GRAPH",
    noGraphSuggestions: "No graph suggestions are available for this data.",
    generatingGraph: "Generating graph...",
    graphReady: "Graph ready.",
    graphFailed: "Unable to generate the graph.",
    downloadGraph: "DOWNLOAD GRAPH",
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
    graphLabel: "GRAFICO",
    questionPlaceholder: "Tu pregunta aparecera aqui.",
    responsePlaceholder: "La respuesta en lenguaje natural aparecera aqui.",
    sqlPlaceholder: "El SQL generado aparecera aqui.",
    dataPlaceholder: "Los datos guardados apareceran aqui.",
    graphPlaceholder: "El grafico generado aparecera aqui.",
    runtimeTitle: "Logs en tiempo real",
    runtimeWaiting: "Esperando sesion...",
    runtimeHidden: "No tienes acceso a los logs en tiempo real.",
    runtimeLoading: "Cargando logs...",
    runtimeEmpty: "Todavia no hay logs disponibles.",
    runtimeError: "No se pudieron cargar los logs.",
    runtimeShowMore: "MOSTRAR MAS LOGS",
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
    textDisabled: "La salida TEXT esta desactivada para esta solicitud.",
    sqlDisabled: "La salida SQL esta desactivada para esta solicitud.",
    graphDisabled: "La salida GRAPH esta desactivada para esta solicitud.",
    graphMode: "GRAPH",
    noGraphSuggestions: "No hay graficos sugeridos para estos datos.",
    generatingGraph: "Generando grafico...",
    graphReady: "Grafico listo.",
    graphFailed: "No se pudo generar el grafico.",
    downloadGraph: "DESCARGAR GRAFICO",
    openQuestion: "Abrir pregunta",
    requestFailed: "La solicitud fallo.",
  },
};

let authToken = "";
let authenticatedEmail = "";
let canViewRuntimeLogs = false;
let currentTheme = "dark";
let currentLanguage = "pt";
let messageHistory = [];
let visibleHistoryCount = HISTORY_PAGE_SIZE;
let selectedMessageId = "";
let runtimeLogLineCount = RUNTIME_LOG_PAGE_SIZE;
let selectedResponseTypes = new Set(DEFAULT_RESPONSE_TYPES);

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

function setGraphicStatus(message, type = "") {
  setStatus(graphStatus, message, type);
}

function setDataText(message, isPlaceholder = false) {
  dataView.textContent = message;
  dataView.classList.toggle("box-placeholder", isPlaceholder);
}

function setDataJson(rows) {
  setDataText(
    rows.length ? JSON.stringify(rows, null, 2) : t("noRows"),
    !rows.length
  );
}

function setGraphText(message, isPlaceholder = false) {
  graphView.replaceChildren();
  graphView.textContent = message;
  graphView.classList.toggle("box-placeholder", isPlaceholder);
}

function setGraphImage(graphPath) {
  const image = document.createElement("img");
  image.className = "graphic-image";
  image.src = graphPath;
  image.alt = "Generated graph";
  graphView.replaceChildren(image);
  graphView.classList.remove("box-placeholder");
}

function renderGraphDownload(graphPath) {
  if (!graphPath) {
    graphDownloadLink.hidden = true;
    graphDownloadLink.removeAttribute("href");
    return;
  }

  graphDownloadLink.hidden = false;
  graphDownloadLink.href = graphPath;
}

function renderResponseTypeButtons() {
  responseButtons.forEach((button) => {
    const isActive = selectedResponseTypes.has(button.dataset.responseType);
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

function getSelectedResponseTypes() {
  return responseButtons
    .map((button) => button.dataset.responseType)
    .filter((responseType) => selectedResponseTypes.has(responseType));
}

function resetResponseTypeSelection() {
  selectedResponseTypes = new Set(DEFAULT_RESPONSE_TYPES);
  renderResponseTypeButtons();
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
  sessionUser.textContent = authenticatedEmail || "-";
  setStatus(sessionStatus, statusMessage, statusType);
}

function renderRuntimeLogPanel() {
  runtimeTitle.textContent = t("runtimeTitle");
  runtimeStatus.className = "status-line";
  runtimePanel.hidden = !canViewRuntimeLogs;
  workspaceShell.classList.toggle("runtime-visible", canViewRuntimeLogs);
  runtimeMoreButton.textContent = t("runtimeShowMore");
  runtimeMoreButton.hidden = !canViewRuntimeLogs;

  if (!canViewRuntimeLogs) {
    runtimeStatus.textContent = t("runtimeHidden");
    setRuntimeLogPlainText(t("runtimeHidden"));
    return;
  }

  if (!runtimeLogView.textContent.trim()) {
    setRuntimeLogPlainText(t("runtimeWaiting"));
  }
}

function scrollRuntimeLogToBottom() {
  runtimeLogView.scrollTop = runtimeLogView.scrollHeight;
}

function scrollRuntimeLogToTop() {
  runtimeLogView.scrollTop = 0;
}

function isRuntimeLogNearBottom() {
  const distanceToBottom =
    runtimeLogView.scrollHeight - runtimeLogView.clientHeight - runtimeLogView.scrollTop;
  return distanceToBottom <= 24;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setRuntimeLogPlainText(message) {
  runtimeLogView.innerHTML = "";
  runtimeLogView.textContent = message;
}

function formatRuntimeLogLine(line) {
  const pattern = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)\s+([A-Za-z0-9_]+)\s+([A-Z]+),\s+(.*)$/;
  const match = String(line).match(pattern);

  if (!match) {
    return `<div class="runtime-log-line"><div class="runtime-log-message">${escapeHtml(line)}</div></div>`;
  }

  const timestamp = match[1];
  const source = match[2];
  const level = match[3].toLowerCase();
  const message = match[4];

  return (
    `<div class="runtime-log-line">` +
      `<div class="runtime-log-meta">` +
        `<span class="runtime-log-time">${escapeHtml(timestamp)}</span>` +
        `<span class="runtime-log-source">${escapeHtml(source)}</span>` +
        `<span class="runtime-log-level ${escapeHtml(level)}">${escapeHtml(match[3])}</span>` +
      `</div>` +
      `<div class="runtime-log-message">${escapeHtml(message)}</div>` +
    `</div>`
  );
}

function setRuntimeLogMarkup(logText) {
  const normalizedText = String(logText || "").trim();

  if (!normalizedText) {
    setRuntimeLogPlainText(t("runtimeEmpty"));
    return;
  }

  const lines = normalizedText
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line);

  runtimeLogView.innerHTML = lines.map((line) => formatRuntimeLogLine(line)).join("");
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
  setBoxLabel(graphLabel, "graphLabel");
  composerLabel.textContent = t("composerLabel");
  questionInput.placeholder = t("inputPlaceholder");
  dataResponseButton.textContent = t("graphMode");
  graphDownloadLink.textContent = t("downloadGraph");
  submitButton.textContent = t("send");

  if (!chatPill.dataset.chatId) {
    chatPill.textContent = t("loading");
  }

  refreshPlaceholder(questionView, "questionPlaceholder");
  refreshPlaceholder(responseView, "responsePlaceholder");
  refreshPlaceholder(sqlView, "sqlPlaceholder");
  refreshPlaceholder(dataView, "dataPlaceholder");
  refreshPlaceholder(graphView, "graphPlaceholder");
  renderSessionUi(authToken ? t("sessionActive") : t("checkingSession"), authToken ? "success" : "");
  renderRuntimeLogPanel();
  renderThemeLabel();
  renderResponseTypeButtons();
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
  authenticatedEmail = payload.email || "";
  canViewRuntimeLogs = Boolean(payload.can_view_runtime_logs);
  runtimeLogLineCount = RUNTIME_LOG_PAGE_SIZE;

  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, authToken);
  window.localStorage.setItem(AUTH_EMAIL_STORAGE_KEY, authenticatedEmail);
  window.localStorage.setItem(
    AUTH_LOG_PERMISSION_STORAGE_KEY,
    canViewRuntimeLogs ? "true" : "false"
  );
  setAuthCookie(authToken);

  agentForm.elements.namedItem("email").value = authenticatedEmail;
  renderSessionUi(t("sessionActive"), "success");
  renderRuntimeLogPanel();
}

function clearStoredSession() {
  authToken = "";
  authenticatedEmail = "";
  canViewRuntimeLogs = false;
  runtimeLogLineCount = RUNTIME_LOG_PAGE_SIZE;

  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_LOG_PERMISSION_STORAGE_KEY);
  clearAuthCookie();

  agentForm.elements.namedItem("email").value = "";
  renderRuntimeLogPanel();
}

function loadStoredSession() {
  authToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) || "";
  authenticatedEmail = window.localStorage.getItem(AUTH_EMAIL_STORAGE_KEY) || "";
  canViewRuntimeLogs =
    window.localStorage.getItem(AUTH_LOG_PERMISSION_STORAGE_KEY) === "true";
  agentForm.elements.namedItem("email").value = authenticatedEmail;
}

function redirectToLogin() {
  clearStoredSession();
  window.location.replace("/login");
}

async function loadRuntimeLogs(scrollMode = "keep") {
  if (!authToken || !canViewRuntimeLogs) {
    renderRuntimeLogPanel();
    return;
  }

  const shouldStickToBottom = scrollMode === "bottom" || (
    scrollMode === "keep" && isRuntimeLogNearBottom()
  );
  runtimeStatus.className = "status-line";
  runtimeStatus.textContent = t("runtimeLoading");

  try {
    const response = await fetch(`/v1/runtime-logs?line_count=${runtimeLogLineCount}`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      cache: "no-store",
    });

    if (response.status === 401) {
      redirectToLogin();
      return;
    }

    if (!response.ok) {
      throw new Error(t("runtimeError"));
    }

    const payload = await response.json();
    canViewRuntimeLogs = Boolean(payload.can_view_runtime_logs);
    renderRuntimeLogPanel();

    if (!canViewRuntimeLogs) {
      return;
    }

    runtimeStatus.textContent = t("sessionActive");
    runtimeStatus.className = "status-line success";
    setRuntimeLogMarkup(payload.logs);
    if (scrollMode === "top") {
      scrollRuntimeLogToTop();
    } else if (shouldStickToBottom) {
      scrollRuntimeLogToBottom();
    }
  } catch (error) {
    runtimeStatus.textContent = t("runtimeError");
    runtimeStatus.className = "status-line error";
    setRuntimeLogPlainText(error.message || t("runtimeError"));
    if (scrollMode === "top") {
      scrollRuntimeLogToTop();
    } else if (shouldStickToBottom) {
      scrollRuntimeLogToBottom();
    }
  }
}

function refreshRuntimeLogsOnActivity(scrollMode = "bottom") {
  if (!canViewRuntimeLogs) {
    renderRuntimeLogPanel();
    return;
  }

  loadRuntimeLogs(scrollMode);
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
    refreshRuntimeLogsOnActivity("bottom");
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

  const inferredResponseTypes = [];
  if (String(entry.response || "").trim()) {
    inferredResponseTypes.push("TEXT");
  }
  if (String(entry.query || "").trim()) {
    inferredResponseTypes.push("SQL");
  }
  if (String(entry.graph_path || "").trim()) {
    inferredResponseTypes.push("GRAPH");
  }

  return {
    mensage_id: String(entry.mensage_id || generateHash()).trim() || generateHash(),
    question,
    response: String(entry.response || ""),
    query: String(entry.query || ""),
    data_path: String(entry.data_path || ""),
    graph_path: String(entry.graph_path || ""),
    selected_graph_pattern: String(entry.selected_graph_pattern || ""),
    response_types: Array.isArray(entry.response_types)
      ? entry.response_types.map((value) => String(value || "").trim()).filter(Boolean)
      : inferredResponseTypes,
    graph_suggestions: Array.isArray(entry.graph_suggestions)
      ? entry.graph_suggestions
        .filter((item) => item && typeof item === "object")
        .map((item) => ({
          id: String(item.id || "").trim(),
          label: String(item.label || "").trim(),
          reason: String(item.reason || "").trim(),
          x_field: String(item.x_field || "").trim(),
          y_field: String(item.y_field || "").trim(),
          hue_field: String(item.hue_field || "").trim(),
        }))
        .filter((item) => item.id)
      : [],
    data_rows: Array.isArray(entry.data_rows) ? entry.data_rows : null,
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

function renderGraphSuggestions(entry, disabled = false) {
  graphSuggestionsView.replaceChildren();

  const suggestions = Array.isArray(entry?.graph_suggestions)
    ? entry.graph_suggestions
    : [];
  if (!suggestions.length) {
    graphSuggestionsView.hidden = true;
    return;
  }

  const fragment = document.createDocumentFragment();
  suggestions.forEach((suggestion) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "graph-suggestion";
    button.dataset.graphPatternId = suggestion.id;
    button.disabled = disabled;
    button.classList.toggle(
      "active",
      suggestion.id === String(entry.selected_graph_pattern || "")
    );
    button.textContent = suggestion.label || suggestion.id;
    button.title = suggestion.reason || suggestion.label || suggestion.id;
    fragment.append(button);
  });

  graphSuggestionsView.append(fragment);
  graphSuggestionsView.hidden = false;
}

function renderDataPanel(rows) {
  if (!rows.length) {
    setDataText(t("noRows"), true);
    return;
  }

  setDataJson(rows);
}

function renderGraphPanel(entry) {
  setGraphicStatus("");
  const graphEnabled = entry.response_types.includes("GRAPH");
  const graphEntry = graphEnabled
    ? entry
    : { ...entry, graph_suggestions: [], graph_path: "", selected_graph_pattern: "" };

  renderGraphSuggestions(graphEntry);
  renderGraphDownload(graphEntry.graph_path);

  if (!graphEnabled) {
    setGraphText(t("graphDisabled"), true);
    return;
  }

  if (entry.graph_path) {
    setGraphImage(entry.graph_path);
    return;
  }

  setGraphText(t("graphPlaceholder"), true);

  if (
    !entry.graph_path
    && !entry.graph_suggestions.length
  ) {
    setGraphicStatus(t("noGraphSuggestions"));
  }
}

function updateMessageEntry(messageId, partialEntry) {
  messageHistory = messageHistory.map((entry) => (
    entry.mensage_id === messageId
      ? { ...entry, ...partialEntry }
      : entry
  ));
  return messageHistory.find((entry) => entry.mensage_id === messageId) || null;
}

async function requestGraphForMessage(messageId, graphPatternId) {
  const entry = messageHistory.find((item) => item.mensage_id === messageId);
  if (!entry) {
    return;
  }

  const session = await validateSessionOrRedirect();
  if (!session) {
    return;
  }

  renderGraphSuggestions(entry, true);
  renderGraphDownload(entry.graph_path);
  setGraphicStatus(t("generatingGraph"));

  try {
    const response = await fetch("/v1/graph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        chat_id: String(chatPill.dataset.chatId || "").trim(),
        question_id: messageId,
        graph_pattern_id: graphPatternId,
      }),
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
      throw new Error(payload.detail || t("graphFailed"));
    }

    const updatedEntry = updateMessageEntry(messageId, {
      graph_path: String(payload.graph_path || ""),
      selected_graph_pattern: String(payload.selected_graph_pattern || ""),
      graph_suggestions: Array.isArray(payload.graph_suggestions)
        ? payload.graph_suggestions
        : entry.graph_suggestions,
    });

    if (selectedMessageId === messageId && updatedEntry) {
      renderDataPanel(Array.isArray(updatedEntry.data_rows) ? updatedEntry.data_rows : []);
      renderGraphPanel(updatedEntry);
    }

    setGraphicStatus(t("graphReady"), "success");
  } catch (error) {
    renderGraphSuggestions(entry, false);
    renderGraphDownload(entry.graph_path);
    setGraphicStatus(error.message || t("graphFailed"), "error");
  }
}

async function showMessageDetails(messageId) {
  const entry = messageHistory.find((item) => item.mensage_id === messageId);
  if (!entry) {
    return;
  }

  selectedMessageId = messageId;
  renderMessageHistory();

  setBoxContent(questionView, entry.question);
  if (entry.response_types.includes("TEXT")) {
    setBoxContent(responseView, entry.response || t("noNaturalResponse"));
  } else {
    setPlaceholder(responseView, t("textDisabled"));
  }

  if (entry.response_types.includes("SQL")) {
    setBoxContent(sqlView, entry.query || t("noSql"));
  } else {
    setPlaceholder(sqlView, t("sqlDisabled"));
  }

  if (!entry.data_path) {
    setDataText(t("noRows"), true);
    renderGraphPanel(entry);
    return;
  }

  const requestedMessageId = messageId;
  setGraphicStatus("");
  setDataText(t("loadingSavedData"), true);
  setGraphText(t("graphPlaceholder"), true);

  try {
    const rows = Array.isArray(entry.data_rows)
      ? entry.data_rows
      : await loadMessageRows(entry.data_path);
    if (selectedMessageId !== requestedMessageId) {
      return;
    }

    const updatedEntry = updateMessageEntry(messageId, { data_rows: rows });
    if (!updatedEntry) {
      return;
    }

    renderDataPanel(rows);
    renderGraphPanel(updatedEntry);
  } catch (error) {
    if (selectedMessageId !== requestedMessageId) {
      return;
    }

    setDataText(error.message || t("unableLoadSavedData"), true);
    renderGraphPanel(entry);
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
    const response = await fetch("/chat_messages.json", {
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

  resetResponseTypeSelection();
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

runtimeMoreButton.addEventListener("click", () => {
  if (!canViewRuntimeLogs) {
    return;
  }

  runtimeLogLineCount += RUNTIME_LOG_PAGE_SIZE;
  refreshRuntimeLogsOnActivity("top");
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
    const value = button.dataset.responseType;
    if (selectedResponseTypes.has(value)) {
      if (selectedResponseTypes.size === 1) {
        return;
      }
      selectedResponseTypes.delete(value);
    } else {
      selectedResponseTypes.add(value);
    }
    renderResponseTypeButtons();
  });
});

graphSuggestionsView.addEventListener("click", (event) => {
  const button = event.target.closest(".graph-suggestion");
  if (!button || !selectedMessageId) {
    return;
  }

  requestGraphForMessage(selectedMessageId, button.dataset.graphPatternId);
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
    graph_path: "",
    selected_graph_pattern: "",
    response_types: getSelectedResponseTypes(),
    graph_suggestions: [],
    data_rows: null,
    created_at: new Date().toISOString(),
  });

  setBoxContent(questionView, question);
  if (selectedResponseTypes.has("TEXT")) {
    setBoxContent(responseView, t("processingRequest"));
  } else {
    setPlaceholder(responseView, t("textDisabled"));
  }

  if (selectedResponseTypes.has("SQL")) {
    setBoxContent(sqlView, t("generatingSql"));
  } else {
    setPlaceholder(sqlView, t("sqlDisabled"));
  }

  renderGraphDownload("");
  renderGraphSuggestions({ graph_suggestions: [] });
  setGraphicStatus("");
  setDataText(t("waitingSavedData"), true);
  if (selectedResponseTypes.has("GRAPH")) {
    setGraphText(t("graphPlaceholder"), true);
  } else {
    setGraphText(t("graphDisabled"), true);
  }
  setStatus(agentStatus, t("callingAgent"));

  const body = {
    email: authenticatedEmail,
    chat_id: chatId,
    question_id: messageId,
    response_types: getSelectedResponseTypes(),
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
    const responseTypes = Array.isArray(result.response_types)
      ? result.response_types
      : getSelectedResponseTypes();

    if (responseTypes.includes("TEXT")) {
      setBoxContent(
        responseView,
        result.response_natural_language || t("noNaturalResponse")
      );
    } else {
      setPlaceholder(responseView, t("textDisabled"));
    }

    if (responseTypes.includes("SQL")) {
      setBoxContent(sqlView, result.response_sql || t("noSql"));
    } else {
      setPlaceholder(sqlView, t("sqlDisabled"));
    }

    const updatedEntry = updateMessageEntry(messageId, {
      response: String(result.response_natural_language || ""),
      query: String(result.response_sql || ""),
      data_path: String(result.data_path || ""),
      graph_path: String(result.graph_path || ""),
      selected_graph_pattern: String(result.selected_graph_pattern || ""),
      response_types: responseTypes,
      graph_suggestions: Array.isArray(result.graph_suggestions)
        ? result.graph_suggestions
        : [],
      data_rows: rows,
    });

    if (updatedEntry) {
      renderDataPanel(rows);
      renderGraphPanel(updatedEntry);
    } else {
      renderDataPanel(rows);
      setGraphText(
        responseTypes.includes("GRAPH") ? t("graphPlaceholder") : t("graphDisabled"),
        true
      );
    }

    renderMessageHistory();
    setStatus(agentStatus, t("responseReceived"), "success");
    setStatus(sessionStatus, t("sessionActive"), "success");
    questionInput.value = "";
    refreshRuntimeLogsOnActivity("bottom");
  } catch (error) {
    setBoxContent(responseView, error.message);
    setPlaceholder(sqlView, t("sqlUnavailable"));
    renderGraphDownload("");
    renderGraphSuggestions({ graph_suggestions: [] });
    setGraphicStatus("");
    setDataText(t("noDataAvailable"), true);
    setGraphText(t("graphPlaceholder"), true);
    setStatus(agentStatus, error.message, "error");
    refreshRuntimeLogsOnActivity("bottom");
  }
});
