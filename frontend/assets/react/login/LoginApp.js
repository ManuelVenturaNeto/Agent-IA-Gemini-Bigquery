import { html, useEffect, useState } from "../shared/cdn.js";
import {
  applyTheme,
  clearStoredSession,
  loadLanguagePreference,
  loadStoredSession,
  loadThemePreference,
  persistSession,
  saveLanguagePreference,
  saveThemePreference,
  setAuthCookie,
} from "../shared/browserStore.js";
import { LanguageSelector } from "../shared/components/LanguageSelector.js";
import { getErrorMessage, requestJson } from "../shared/http.js";
import { buildClassName } from "../shared/utils.js";
import { createLoginTranslator } from "./translations.js";

function redirectToHome() {
  window.location.replace("/");
}

export function LoginApp() {
  const [language, setLanguage] = useState(loadLanguagePreference());
  const [theme, setTheme] = useState(loadThemePreference());
  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("demo_password");
  const [status, setStatus] = useState({
    message: "",
    type: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const t = createLoginTranslator(language);

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

  useEffect(() => {
    let isCancelled = false;

    async function validateExistingSession() {
      const storedToken = loadStoredSession().token;
      if (!storedToken) {
        return;
      }

      const { response } = await requestJson("/v1/session", {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      });

      if (isCancelled) {
        return;
      }

      if (!response.ok) {
        clearStoredSession();
        return;
      }

      setAuthCookie(storedToken);
      redirectToHome();
    }

    validateExistingSession();

    return () => {
      isCancelled = true;
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus({
      message: t("connecting"),
      type: "",
    });
    setIsSubmitting(true);

    try {
      const { response, payload } = await requestJson("/v1/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!response.ok) {
        throw new Error(getErrorMessage(payload, t("invalid")));
      }

      persistSession(payload);
      redirectToHome();
    } catch (error) {
      clearStoredSession();
      setStatus({
        message: error.message || t("invalid"),
        type: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  const themeLabel = `${t("theme")}: ${theme === "light" ? t("themeLight") : t("themeDark")}`;

  return html`
    <main className="auth-shell">
      <section className="auth-card">
        <p className="console-title">${t("title")}</p>

        <div className="auth-toolbar">
          <${LanguageSelector}
            currentLanguage=${language}
            onSelect=${setLanguage}
          />

          <button
            type="button"
            className="theme-toggle"
            onClick=${() => setTheme((currentTheme) => (
              currentTheme === "light" ? "dark" : "light"
            ))}
          >
            ${themeLabel}
          </button>
        </div>

        <form className="auth-form" onSubmit=${handleSubmit}>
          <label className="composer-label" htmlFor="login-email">${t("email")}</label>
          <input
            id="login-email"
            type="email"
            name="email"
            value=${email}
            autoComplete="email"
            required
            onChange=${(event) => setEmail(event.target.value)}
          />

          <label className="composer-label" htmlFor="login-password">${t("password")}</label>
          <input
            id="login-password"
            type="password"
            name="password"
            value=${password}
            autoComplete="current-password"
            required
            onChange=${(event) => setPassword(event.target.value)}
          />

          <button
            type="submit"
            className="submit-button"
            disabled=${isSubmitting}
          >
            ${isSubmitting ? t("connecting") : t("submit")}
          </button>

          <p className=${buildClassName("status-line", status.type)}>
            ${status.message}
          </p>
        </form>
      </section>
    </main>
  `;
}
