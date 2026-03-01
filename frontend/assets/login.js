const loginForm = document.getElementById("login-form");
const loginStatus = document.getElementById("login-status");
const pageTitle = document.getElementById("login-page-title");
const usernameLabel = document.getElementById("login-username-label");
const passwordLabel = document.getElementById("login-password-label");
const submitButton = document.getElementById("login-submit");
const themeToggle = document.getElementById("login-theme-toggle");
const languageButtons = Array.from(document.querySelectorAll("[data-language]"));

const LANGUAGE_STORAGE_KEY = "ia-agent-language";
const THEME_STORAGE_KEY = "ia-agent-theme";
const AUTH_TOKEN_STORAGE_KEY = "ia-agent-auth-token";
const AUTH_USERNAME_STORAGE_KEY = "ia-agent-auth-user";
const AUTH_EMAIL_STORAGE_KEY = "ia-agent-auth-email";
const AUTH_COOKIE_KEY = "ia_agent_auth_token";

const translations = {
  pt: {
    title: "LOGIN DO AGENTE IA",
    username: "USUARIO",
    password: "SENHA",
    submit: "ENTRAR",
    theme: "TEMA",
    themeDark: "ESCURO",
    themeLight: "CLARO",
    connecting: "Conectando...",
    invalid: "Falha no login.",
  },
  en: {
    title: "IA AGENT LOGIN",
    username: "USERNAME",
    password: "PASSWORD",
    submit: "LOGIN",
    theme: "THEME",
    themeDark: "DARK",
    themeLight: "LIGHT",
    connecting: "Connecting...",
    invalid: "Login failed.",
  },
  es: {
    title: "LOGIN DEL AGENTE IA",
    username: "USUARIO",
    password: "CLAVE",
    submit: "ENTRAR",
    theme: "TEMA",
    themeDark: "OSCURO",
    themeLight: "CLARO",
    connecting: "Conectando...",
    invalid: "Error de inicio de sesion.",
  },
};

let currentLanguage = "pt";
let currentTheme = "dark";

function t(key) {
  return translations[currentLanguage]?.[key] || translations.pt[key] || key;
}

function setStatus(message, type = "") {
  loginStatus.textContent = message;
  loginStatus.className = `status-line ${type}`.trim();
}

function activateButton(buttons, activeButton) {
  buttons.forEach((button) => {
    button.classList.toggle("active", button === activeButton);
  });
}

function renderThemeLabel() {
  const themeState = currentTheme === "light" ? t("themeLight") : t("themeDark");
  themeToggle.textContent = `${t("theme")}: ${themeState}`;
}

function updateStaticText() {
  document.documentElement.lang = currentLanguage;
  pageTitle.textContent = t("title");
  usernameLabel.textContent = t("username");
  passwordLabel.textContent = t("password");
  submitButton.textContent = t("submit");
  renderThemeLabel();
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

function clearStoredSession() {
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_USERNAME_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY);
  clearAuthCookie();
}

function persistSession(payload) {
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, payload.access_token);
  window.localStorage.setItem(AUTH_USERNAME_STORAGE_KEY, payload.username || "");
  window.localStorage.setItem(AUTH_EMAIL_STORAGE_KEY, payload.email || "");
  setAuthCookie(payload.access_token);
}

async function redirectIfSessionIsValid() {
  const token = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
  if (!token) {
    return;
  }

  try {
    const response = await fetch("/v1/session", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      clearStoredSession();
      return;
    }

    setAuthCookie(token);
    window.location.replace("/");
  } catch {
    clearStoredSession();
  }
}

loadLanguagePreference();
loadThemePreference();
redirectIfSessionIsValid();

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

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(loginForm);
  setStatus(t("connecting"));

  try {
    const response = await fetch("/v1/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || t("invalid"));
    }

    persistSession(payload);
    window.location.replace("/");
  } catch (error) {
    clearStoredSession();
    setStatus(error.message, "error");
  }
});
