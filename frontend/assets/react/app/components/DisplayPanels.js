import { html } from "../../shared/cdn.js";
import { buildClassName } from "../../shared/utils.js";
import { formatBoxLabel } from "../displayState.js";

export function DisplayPanels({
  t,
  displayState,
  onRequestGraph,
}) {
  return html`
    <section className="display-stack">
      <article className="display-box question-box">
        <span className="box-label">${formatBoxLabel(t("questionLabel"))}</span>
        <div className=${buildClassName(
          "box-content",
          displayState.question.isPlaceholder && "box-placeholder",
        )}>
          ${displayState.question.content}
        </div>
      </article>

      <article className="display-box response-box">
        <span className="box-label">${formatBoxLabel(t("responseLabel"))}</span>
        <div className=${buildClassName(
          "box-content",
          "box-scroll",
          displayState.response.isPlaceholder && "box-placeholder",
        )}>
          ${displayState.response.content}
        </div>
      </article>

      <article className="display-box sql-box">
        <span className="box-label">${formatBoxLabel(t("sqlLabel"))}</span>
        <pre className=${buildClassName(
          "box-content",
          "box-scroll",
          displayState.sql.isPlaceholder && "box-placeholder",
        )}>
          ${displayState.sql.content}
        </pre>
      </article>

      <article className="display-box data-box">
        <span className="box-label">${formatBoxLabel(t("dataLabel"))}</span>
        <pre className=${buildClassName(
          "box-content",
          "box-scroll",
          displayState.data.isPlaceholder && "box-placeholder",
        )}>
          ${displayState.data.content}
        </pre>
      </article>

      <article className="display-box graph-box">
        <span className="box-label">${formatBoxLabel(t("graphLabel"))}</span>

        <div className="graph-controls">
          <div
            className="graph-suggestions"
            hidden=${!displayState.graph.showSuggestions}
          >
            ${displayState.graph.suggestions.map((suggestion) => html`
              <button
                key=${suggestion.id}
                type="button"
                className=${buildClassName(
                  "graph-suggestion",
                  suggestion.id === displayState.graph.selectedPatternId && "active",
                )}
                title=${suggestion.reason || suggestion.label || suggestion.id}
                disabled=${displayState.graph.disableSuggestions}
                onClick=${() => onRequestGraph(suggestion.id)}
              >
                ${suggestion.label || suggestion.id}
              </button>
            `)}
          </div>

          <a
            className="history-more graph-download"
            href=${displayState.graph.downloadHref}
            download=${true}
            hidden=${!displayState.graph.showDownload}
          >
            ${t("downloadGraph")}
          </a>
        </div>

        <p className=${buildClassName("status-line", displayState.graph.statusType)}>
          ${displayState.graph.status}
        </p>

        <div className=${buildClassName(
          "box-content",
          "box-scroll",
          "graphic-content",
          displayState.graph.isPlaceholder && "box-placeholder",
        )}>
          ${displayState.graph.imagePath
            ? html`
              <img
                className="graphic-image"
                src=${displayState.graph.imagePath}
                alt=${t("graphLabel")}
              />
            `
            : displayState.graph.content}
        </div>
      </article>
    </section>
  `;
}
