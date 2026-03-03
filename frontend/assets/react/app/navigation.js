import { clearStoredSession } from "../shared/browserStore.js";

export function redirectToLogin() {
  clearStoredSession();
  window.location.replace("/login");
}
