import { createRoot, html } from "../shared/cdn.js";
import { AppShell } from "./AppShell.js";

const rootElement = document.getElementById("app-root");

if (rootElement) {
  const root = createRoot(rootElement);
  root.render(html`<${AppShell} />`);
}
