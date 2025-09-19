import React from "react";
import { createRoot } from "react-dom/client";
import Game from "./SeaTreasureHunt.jsx"; // paste your code into this file

function mount(selector = "#treasure-game-root") {
  const el = document.querySelector(selector);
  if (!el) return;
  const root = createRoot(el);
  root.render(<Game />);
}

// auto-mount if the placeholder exists:
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => mount());
} else {
  mount();
}

export { mount };
