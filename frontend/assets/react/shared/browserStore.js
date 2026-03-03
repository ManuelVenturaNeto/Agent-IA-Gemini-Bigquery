import {
  AUTH_COOKIE_KEY,
  DEFAULT_LANGUAGE,
  DEFAULT_THEME,
  STORAGE_KEYS,
} from "./constants.js";

function readStorage(key, fallback = "") {
  try {
    const value = window.localStorage.getItem(key);
    return value === null ? fallback : value;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    return;
  }
}

function removeStorage(key) {
  try {
    window.localStorage.removeItem(key);
  } catch {
    return;
  }
}

export function loadLanguagePreference() {
  const value = readStorage(STORAGE_KEYS.language, DEFAULT_LANGUAGE);
  return value === "en" || value === "es" ? value : DEFAULT_LANGUAGE;
}

export function saveLanguagePreference(language) {
  writeStorage(STORAGE_KEYS.language, language);
}

export function applyTheme(theme) {
  const normalizedTheme = theme === "light" ? "light" : "dark";
  document.body.classList.toggle("light-theme", normalizedTheme === "light");
  return normalizedTheme;
}

export function loadThemePreference() {
  const storedTheme = readStorage(STORAGE_KEYS.theme, DEFAULT_THEME);
  return storedTheme === "light" ? "light" : DEFAULT_THEME;
}

export function saveThemePreference(theme) {
  writeStorage(STORAGE_KEYS.theme, theme);
}

export function setAuthCookie(token) {
  document.cookie = `${AUTH_COOKIE_KEY}=${encodeURIComponent(token)}; path=/; SameSite=Lax`;
}

function clearAuthCookie() {
  document.cookie = `${AUTH_COOKIE_KEY}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
}

export function persistSession(payload) {
  const token = String(payload?.access_token || "").trim();
  if (!token) {
    return;
  }

  writeStorage(STORAGE_KEYS.authToken, token);
  writeStorage(STORAGE_KEYS.authEmail, String(payload?.email || "").trim());
  writeStorage(
    STORAGE_KEYS.authLogPermission,
    payload?.can_view_runtime_logs ? "true" : "false",
  );
  setAuthCookie(token);
}

export function loadStoredSession() {
  return {
    token: readStorage(STORAGE_KEYS.authToken, ""),
    email: readStorage(STORAGE_KEYS.authEmail, ""),
    canViewRuntimeLogs: readStorage(STORAGE_KEYS.authLogPermission, "") === "true",
  };
}

export function clearStoredSession() {
  removeStorage(STORAGE_KEYS.authToken);
  removeStorage(STORAGE_KEYS.authEmail);
  removeStorage(STORAGE_KEYS.authLogPermission);
  clearAuthCookie();
}
