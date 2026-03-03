import { html } from "../../shared/cdn.js";

export function RuntimeLogsPanel({
  t,
  canViewRuntimeLogs,
  runtimeState,
  onShowMoreRuntimeLogs,
}) {
  return html`
    <aside className="runtime-panel" hidden=${!canViewRuntimeLogs}>
      <div className="runtime-header">
        <span className="rail-dot"></span>
        <p className="history-title">${t("runtimeTitle")}</p>
      </div>

      <p className="status-line">${runtimeState.status || t("runtimeWaiting")}</p>

      <div className="runtime-actions">
        <button
          type="button"
          className="history-more"
          disabled=${runtimeState.loading}
          onClick=${onShowMoreRuntimeLogs}
        >
          ${t("runtimeShowMore")}
        </button>
      </div>

      <div className="runtime-log-view" role="log" aria-live="polite">
        ${runtimeState.logs || ""}
      </div>
    </aside>
  `;
}
