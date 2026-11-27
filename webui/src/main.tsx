import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import "./lib/i18n";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {/* Keep route changes in sync with sidebar clicks and task creation (#397). */}
    <BrowserRouter useTransitions={false}>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
