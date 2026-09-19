import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

/* global Office */
const render = () => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
};

if (typeof Office !== "undefined") {
  Office.onReady(() => render());
} else {
  // Allows local UI development outside the actual Word host.
  render();
}
