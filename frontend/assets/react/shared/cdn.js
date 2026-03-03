import React, { useEffect, useState } from "../vendor/react.bundle.mjs";
import { createRoot } from "../vendor/react-dom-client.bundle.mjs";
import htm from "../vendor/htm.bundle.mjs";

const html = htm.bind(React.createElement);

export { React, createRoot, html, useEffect, useState };
