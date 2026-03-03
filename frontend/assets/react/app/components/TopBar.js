import { html } from "../../shared/cdn.js";
import { buildClassName } from "../../shared/utils.js";
import { LanguageSelector } from "../../shared/components/LanguageSelector.js";

export function TopBar({
  t,
  language,
  onLanguageChange,
  themeLabel,
  onToggleTheme,
  email,
  sessionStatus,
  onLogout,
}) {
  return html`
    <header className="top-strip">
      <p className="console-title">${t("consoleTitle")}</p>

      <div className="toolbar-stack">
        <div className="toolbar-controls">
          <${LanguageSelector}
            currentLanguage=${language}
            onSelect=${onLanguageChange}
          />

          <button
            type="button"
            className="theme-toggle"
            onClick=${onToggleTheme}
          >
            ${themeLabel}
          </button>
        </div>

        <div className="session-meta">
          <p className="session-user">${email || "-"}</p>
          <p className=${buildClassName("status-chip", sessionStatus.type)}>
            ${sessionStatus.message || t("checkingSession")}
          </p>
          <button
            type="button"
            className="action-pill"
            onClick=${onLogout}
          >
            ${t("logout")}
          </button>
        </div>
      </div>
    </header>
  `;
}
