import {
  buildAuthHeaders,
  getErrorMessage,
  requestJson,
} from "../shared/http.js";

export async function validateSessionRequest(token) {
  return requestJson("/v1/session", {
    headers: buildAuthHeaders(token),
  });
}

export async function loadChatHistoryRequest() {
  return requestJson("/chat_messages.json");
}

export async function loadRuntimeLogsRequest(token, lineCount) {
  return requestJson(`/v1/runtime-logs?line_count=${lineCount}`, {
    headers: buildAuthHeaders(token),
  });
}

export async function askAgentRequest(token, body) {
  return requestJson("/v1/ask", {
    method: "POST",
    headers: buildAuthHeaders(token, {
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(body),
  });
}

export async function requestGraphRequest(token, body) {
  return requestJson("/v1/graph", {
    method: "POST",
    headers: buildAuthHeaders(token, {
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(body),
  });
}

export async function loadMessageRowsRequest(dataPath, fallbackMessage) {
  const response = await fetch(dataPath, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(fallbackMessage);
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  return Array.isArray(payload) ? payload : [];
}

export function resolveApiError(payload, fallbackMessage) {
  return getErrorMessage(payload, fallbackMessage);
}
