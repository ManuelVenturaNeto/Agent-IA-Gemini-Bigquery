import { createHashId, normalizeArray } from "../shared/utils.js";

function normalizeGraphSuggestions(value) {
  return normalizeArray(value)
    .filter((item) => item && typeof item === "object")
    .map((item) => ({
      id: String(item.id || "").trim(),
      label: String(item.label || "").trim(),
      reason: String(item.reason || "").trim(),
      x_field: String(item.x_field || "").trim(),
      y_field: String(item.y_field || "").trim(),
      hue_field: String(item.hue_field || "").trim(),
    }))
    .filter((item) => item.id);
}

export function normalizeMessage(entry) {
  if (!entry || typeof entry !== "object") {
    return null;
  }

  const question = String(entry.question || "").trim();
  if (!question) {
    return null;
  }

  const inferredResponseTypes = [];
  if (String(entry.response || "").trim()) {
    inferredResponseTypes.push("TEXT");
  }
  if (String(entry.query || "").trim()) {
    inferredResponseTypes.push("SQL");
  }
  if (String(entry.graph_path || "").trim()) {
    inferredResponseTypes.push("GRAPH");
  }

  const responseTypes = Array.isArray(entry.response_types)
    ? entry.response_types
      .map((value) => String(value || "").trim().toUpperCase())
      .filter(Boolean)
    : inferredResponseTypes;

  return {
    mensage_id: String(entry.mensage_id || createHashId()).trim() || createHashId(),
    question,
    response: String(entry.response || ""),
    query: String(entry.query || ""),
    data_path: String(entry.data_path || ""),
    graph_path: String(entry.graph_path || ""),
    selected_graph_pattern: String(entry.selected_graph_pattern || ""),
    response_types: responseTypes,
    graph_suggestions: normalizeGraphSuggestions(entry.graph_suggestions),
    data_rows: Array.isArray(entry.data_rows) ? entry.data_rows : null,
    data_loading: Boolean(entry.data_loading),
    data_error: String(entry.data_error || ""),
    graph_error: String(entry.graph_error || ""),
    is_pending: Boolean(entry.is_pending),
    created_at: String(entry.created_at || ""),
  };
}

export function createPendingMessage({ messageId, question, responseTypes }) {
  return normalizeMessage({
    mensage_id: messageId,
    question,
    response_types: responseTypes,
    created_at: new Date().toISOString(),
    data_rows: null,
    data_loading: false,
    data_error: "",
    graph_error: "",
    is_pending: true,
  });
}

export function patchMessageCollection(messages, messageId, patch) {
  return messages.map((entry) => (
    entry.mensage_id === messageId
      ? normalizeMessage({ ...entry, ...patch }) || { ...entry, ...patch }
      : entry
  ));
}

export function sortMessageCollection(messages) {
  return [...messages]
    .map((entry, index) => ({ ...entry, sort_index: index }))
    .sort((left, right) => {
      const leftTime = Date.parse(left.created_at);
      const rightTime = Date.parse(right.created_at);

      if (!Number.isNaN(leftTime) && !Number.isNaN(rightTime) && leftTime !== rightTime) {
        return rightTime - leftTime;
      }

      if (!Number.isNaN(rightTime)) {
        return 1;
      }

      if (!Number.isNaN(leftTime)) {
        return -1;
      }

      return right.sort_index - left.sort_index;
    })
    .map(({ sort_index, ...entry }) => entry);
}
