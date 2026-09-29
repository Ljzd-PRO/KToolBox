import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./lib/i18n";
import "./styles.css";

// 空白页 bug 兜底（2026-09-29）：根级 ErrorBoundary——渲染异常显示可见兜底 UI 而非白屏，并上报 /api/v1/client-error
ReactDOM.createRoot(document.getElementById("root")!, {
  // React 19 根级未捕获错误兜底（ErrorBoundary 自身之外的 root 级错误——记录 + 上报，白屏前留痕）
  onUncaughtError: (error, errorInfo) => {
    console.error("[root] uncaught render error", error, errorInfo);
    try {
      navigator.sendBeacon(
        "/api/v1/client-error",
        JSON.stringify({
          type: "root-uncaught",
          message: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack ?? "" : "",
          componentStack: errorInfo?.componentStack ?? "",
          ts: Date.now(),
          href: location.href,
          ua: navigator.userAgent,
        }),
      );
    } catch {
      /* noop */
    }
  },
}).render(
  <React.StrictMode>
    <ErrorBoundary label="root">
      {/* 视图不更新 bug 根因修复（2026-09-29 实测确认）：react-router v7 默认 startTransition 导航，
          某次 location 更新会被 React 丢弃（URL 变但视图停留在旧页）——useTransitions={false} 恢复同步导航 */}
      <BrowserRouter useTransitions={false}>
        <App />
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
);
