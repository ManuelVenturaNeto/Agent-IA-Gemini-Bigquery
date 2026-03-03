import { html } from "../shared/cdn.js";
import { HISTORY_PAGE_SIZE } from "../shared/constants.js";
import { buildClassName } from "../shared/utils.js";
import { buildDisplayState } from "./displayState.js";
import { useAnalyticalAgentController } from "./useAnalyticalAgentController.js";
import { ChatRail } from "./components/ChatRail.js";
import { ComposerPanel } from "./components/ComposerPanel.js";
import { DisplayPanels } from "./components/DisplayPanels.js";
import { RuntimeLogsPanel } from "./components/RuntimeLogsPanel.js";
import { TopBar } from "./components/TopBar.js";

export function AppShell() {
  const controller = useAnalyticalAgentController();
  const themeLabel = `${controller.t("theme")}: ${controller.theme === "light"
    ? controller.t("themeLight")
    : controller.t("themeDark")}`;
  const showMoreLabel = controller.t("showMore").replace(
    "{count}",
    String(HISTORY_PAGE_SIZE),
  );
  const displayState = buildDisplayState({
    selectedMessage: controller.selectedMessage,
    graphBusyId: controller.graphBusyId,
    t: controller.t,
  });

  return html`
    <main className="dashboard-shell">
      <section className=${buildClassName(
        "workspace-shell",
        controller.canViewRuntimeLogs && "runtime-visible",
      )}>
        <section className="console-frame">
          <${ChatRail}
            t=${controller.t}
            chatId=${controller.chatId}
            visibleMessages=${controller.visibleMessages}
            selectedMessageId=${controller.selectedMessageId}
            hasMoreHistory=${controller.hasMoreHistory}
            showMoreLabel=${showMoreLabel}
            onSelectMessage=${controller.selectMessage}
            onShowMoreHistory=${controller.showMoreHistory}
          />

          <section className="main-column">
            <${TopBar}
              t=${controller.t}
              language=${controller.language}
              onLanguageChange=${controller.setLanguage}
              themeLabel=${themeLabel}
              onToggleTheme=${controller.toggleTheme}
              email=${controller.email}
              sessionStatus=${controller.sessionStatus}
              onLogout=${controller.logout}
            />

            <${DisplayPanels}
              t=${controller.t}
              displayState=${displayState}
              onRequestGraph=${controller.requestGraph}
            />

            <${ComposerPanel}
              t=${controller.t}
              question=${controller.question}
              onQuestionChange=${controller.setQuestion}
              questionContext=${controller.questionContext}
              onSelectContext=${controller.selectContext}
              responseTypes=${controller.responseTypes}
              onToggleResponseType=${controller.toggleResponseType}
              isSubmitting=${controller.isSubmitting}
              agentStatus=${controller.agentStatus}
              onSubmit=${controller.submitQuestion}
            />
          </section>
        </section>

        <${RuntimeLogsPanel}
          t=${controller.t}
          canViewRuntimeLogs=${controller.canViewRuntimeLogs}
          runtimeState=${controller.runtimeState}
          onShowMoreRuntimeLogs=${controller.showMoreRuntimeLogs}
        />
      </section>
    </main>
  `;
}
