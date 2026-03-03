export function buildClassName(...parts) {
  return parts.filter(Boolean).join(" ");
}

export function createHashId(length = 32) {
  if (window.crypto && typeof window.crypto.getRandomValues === "function") {
    const bytes = new Uint8Array(Math.max(2, Math.floor(length / 2)));
    window.crypto.getRandomValues(bytes);
    return Array.from(
      bytes,
      (byte) => byte.toString(16).padStart(2, "0"),
    ).join("");
  }

  const fallback = `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`;
  return fallback.padEnd(length, "0").slice(0, length);
}

export function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}
