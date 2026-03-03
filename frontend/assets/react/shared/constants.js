export const STORAGE_KEYS = {
  language: "ia-agent-language",
  theme: "ia-agent-theme",
  authToken: "ia-agent-auth-token",
  authEmail: "ia-agent-auth-email",
  authLogPermission: "ia-agent-log-permission",
};

export const AUTH_COOKIE_KEY = "ia_agent_auth_token";
export const DEFAULT_LANGUAGE = "pt";
export const DEFAULT_THEME = "dark";
export const DEFAULT_RESPONSE_TYPES = ["TEXT", "SQL"];
export const HISTORY_PAGE_SIZE = 5;
export const RUNTIME_LOG_PAGE_SIZE = 60;

export const CONTEXT_OPTIONS = [
  { id: "TRAVEL", value: "TRAVEL" },
  { id: "EXPENSE", value: "EXPENSE" },
  { id: "SERVICE", value: "SERVICE" },
  { id: "COMMERCIAL", value: "COMMERCIAL" },
  { id: "CS", value: "" },
  { id: "OTHERS", value: "" },
];

export const RESPONSE_OPTIONS = ["TEXT", "SQL", "GRAPH"];
