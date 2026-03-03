import { html } from "../cdn.js";
import { buildClassName } from "../utils.js";

const SUPPORTED_LANGUAGES = ["pt", "en", "es"];

export function LanguageSelector({
  currentLanguage,
  onSelect,
  ariaLabel = "Language selector",
}) {
  return html`
    <div className="language-toggle" role="group" aria-label=${ariaLabel}>
      ${SUPPORTED_LANGUAGES.map((language) => html`
        <button
          key=${language}
          type="button"
          className=${buildClassName(
            "select-pill",
            "language-pill",
            currentLanguage === language && "active",
          )}
          onClick=${() => onSelect(language)}
        >
          ${language.toUpperCase()}
        </button>
      `)}
    </div>
  `;
}
