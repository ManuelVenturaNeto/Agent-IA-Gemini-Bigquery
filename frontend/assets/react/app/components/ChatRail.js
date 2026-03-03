import { html } from "../../shared/cdn.js";
import { buildClassName } from "../../shared/utils.js";

export function ChatRail({
  t,
  chatId,
  visibleMessages,
  selectedMessageId,
  hasMoreHistory,
  showMoreLabel,
  onSelectMessage,
  onShowMoreHistory,
}) {
  return html`
    <aside className="chat-rail">
      <div className="rail-header">
        <span className="rail-dot"></span>
        <p>${t("chats")}</p>
      </div>

      <div className="chat-list" role="list" aria-label="Current chat">
        <button type="button" className="chat-pill active" data-chat-id=${chatId || ""}>
          ${chatId || t("loading")}
        </button>
      </div>

      <div className="history-panel">
        <p className="history-title">${t("previousQuestions")}</p>
        <div className="question-history" role="log" aria-live="polite">
          ${visibleMessages.length
            ? visibleMessages.map((entry) => html`
              <button
                key=${entry.mensage_id}
                type="button"
                className=${buildClassName(
                  "history-item",
                  entry.mensage_id === selectedMessageId && "active",
                )}
                title=${entry.mensage_id}
                aria-label=${`${t("openQuestion")} ${entry.mensage_id}`}
                onClick=${() => onSelectMessage(entry.mensage_id)}
              >
                <p className="history-question">${entry.question}</p>
              </button>
            `)
            : html`<p className="question-history-empty">${t("historyEmpty")}</p>`}
        </div>

        <button
          type="button"
          className="history-more"
          hidden=${!hasMoreHistory}
          disabled=${!hasMoreHistory}
          onClick=${onShowMoreHistory}
        >
          ${showMoreLabel}
        </button>
      </div>
    </aside>
  `;
}
