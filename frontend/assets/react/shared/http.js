export async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    ...options,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  return {
    response,
    payload,
  };
}

export function getErrorMessage(payload, fallbackMessage) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return fallbackMessage;
  }

  return String(payload.detail || payload.message || fallbackMessage);
}

export function buildAuthHeaders(token, extraHeaders = {}) {
  return token
    ? {
      ...extraHeaders,
      Authorization: `Bearer ${token}`,
    }
    : extraHeaders;
}
