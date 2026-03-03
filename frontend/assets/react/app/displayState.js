function createPanelState(content, isPlaceholder) {
  return {
    content,
    isPlaceholder,
  };
}

function formatRows(rows) {
  return JSON.stringify(rows, null, 2);
}

export function formatBoxLabel(label) {
  return `<${label}>`;
}

export function buildDisplayState({
  selectedMessage,
  graphBusyId,
  t,
}) {
  const initialState = {
    question: createPanelState(t("questionPlaceholder"), true),
    response: createPanelState(t("responsePlaceholder"), true),
    sql: createPanelState(t("sqlPlaceholder"), true),
    data: createPanelState(t("dataPlaceholder"), true),
    graph: {
      content: t("graphPlaceholder"),
      isPlaceholder: true,
      imagePath: "",
      status: "",
      statusType: "",
      suggestions: [],
      selectedPatternId: "",
      disableSuggestions: false,
      showSuggestions: false,
      downloadHref: "#",
      showDownload: false,
    },
  };

  if (!selectedMessage) {
    return initialState;
  }

  initialState.question = createPanelState(selectedMessage.question, false);

  if (selectedMessage.response_types.includes("TEXT")) {
    if (selectedMessage.is_pending) {
      initialState.response = createPanelState(t("processingRequest"), false);
    } else if (selectedMessage.response) {
      initialState.response = createPanelState(selectedMessage.response, false);
    } else {
      initialState.response = createPanelState(t("noNaturalResponse"), true);
    }
  } else {
    initialState.response = createPanelState(t("textDisabled"), true);
  }

  if (selectedMessage.response_types.includes("SQL")) {
    if (selectedMessage.is_pending) {
      initialState.sql = createPanelState(t("generatingSql"), false);
    } else if (selectedMessage.query) {
      initialState.sql = createPanelState(selectedMessage.query, false);
    } else {
      initialState.sql = createPanelState(t("noSql"), true);
    }
  } else {
    initialState.sql = createPanelState(t("sqlDisabled"), true);
  }

  if (selectedMessage.is_pending) {
    initialState.data = createPanelState(t("waitingSavedData"), true);
  } else if (selectedMessage.data_loading) {
    initialState.data = createPanelState(t("loadingSavedData"), true);
  } else if (selectedMessage.data_error) {
    initialState.data = createPanelState(selectedMessage.data_error, true);
  } else {
    const rows = Array.isArray(selectedMessage.data_rows) ? selectedMessage.data_rows : [];
    initialState.data = rows.length
      ? createPanelState(formatRows(rows), false)
      : createPanelState(t("noRows"), true);
  }

  const graphEnabled = selectedMessage.response_types.includes("GRAPH");
  const hasGraphImage = Boolean(selectedMessage.graph_path);
  const hasSuggestions = graphEnabled && selectedMessage.graph_suggestions.length > 0;

  initialState.graph = {
    content: graphEnabled ? t("graphPlaceholder") : t("graphDisabled"),
    isPlaceholder: !hasGraphImage,
    imagePath: hasGraphImage ? selectedMessage.graph_path : "",
    status: "",
    statusType: "",
    suggestions: graphEnabled ? selectedMessage.graph_suggestions : [],
    selectedPatternId: graphEnabled ? selectedMessage.selected_graph_pattern : "",
    disableSuggestions: graphBusyId === selectedMessage.mensage_id,
    showSuggestions: hasSuggestions,
    downloadHref: selectedMessage.graph_path || "#",
    showDownload: hasGraphImage,
  };

  if (graphBusyId === selectedMessage.mensage_id) {
    initialState.graph.status = t("generatingGraph");
  } else if (selectedMessage.graph_error) {
    initialState.graph.status = selectedMessage.graph_error;
    initialState.graph.statusType = "error";
  } else if (
    graphEnabled
    && !hasGraphImage
    && !selectedMessage.is_pending
    && !hasSuggestions
  ) {
    initialState.graph.status = t("noGraphSuggestions");
  }

  return initialState;
}
