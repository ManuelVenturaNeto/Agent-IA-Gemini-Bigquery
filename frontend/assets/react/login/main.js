import { createRoot, html } from "../shared/cdn.js";
import { LoginApp } from "./LoginApp.js";

const rootElement = document.getElementById("login-root");

if (rootElement) {
  const root = createRoot(rootElement);
  root.render(html`<${LoginApp} />`);
}
