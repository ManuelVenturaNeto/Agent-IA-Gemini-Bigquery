import { html } from "../../shared/cdn.js";
import {
  CONTEXT_OPTIONS,
  RESPONSE_OPTIONS,
} from "../../shared/constants.js";
import { buildClassName } from "../../shared/utils.js";

export function ComposerPanel({
  t,
  question,
  onQuestionChange,
  questionContext,
  onSelectContext,
  responseTypes,
  onToggleResponseType,
  isSubmitting,
  agentStatus,
  onSubmit,
}) {
  return html`
    <section className="control-grid">
      <div className="button-grid" role="group" aria-label="Context selector">
        ${CONTEXT_OPTIONS.map((option) => html`
          <button
            key=${option.id}
            type="button"
            className=${buildClassName(
              "select-pill",
              questionContext === option.id && "active",
            )}
            onClick=${() => onSelectContext(option.id)}
          >
            ${option.id}
          </button>
        `)}
      </div>

      <form className="composer-panel" onSubmit=${onSubmit}>
        <label className="composer-label" htmlFor="question-input">
          ${t("composerLabel")}
        </label>

        <textarea
          id="question-input"
          name="question"
          rows="4"
          value=${question}
          placeholder=${t("inputPlaceholder")}
          required
          onChange=${(event) => onQuestionChange(event.target.value)}
        ></textarea>

        <div className="composer-actions">
          <div className="button-row" role="group" aria-label="Response type selector">
            ${RESPONSE_OPTIONS.map((option) => html`
              <button
                key=${option}
                type="button"
                className=${buildClassName(
                  "select-pill",
                  responseTypes.includes(option) && "active",
                )}
                aria-pressed=${responseTypes.includes(option)}
                onClick=${() => onToggleResponseType(option)}
              >
                ${option}
              </button>
            `)}
          </div>

          <button
            type="submit"
            className="submit-button"
            disabled=${isSubmitting}
          >
            ${isSubmitting ? t("processingRequest") : t("send")}
          </button>
        </div>

        <p className=${buildClassName("status-line", agentStatus.type)}>
          ${agentStatus.message}
        </p>
      </form>
    </section>
  `;
}
