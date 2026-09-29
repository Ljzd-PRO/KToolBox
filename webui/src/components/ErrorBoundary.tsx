import { Component, type ErrorInfo, type ReactNode } from "react";

/**
 * 前端空白页 bug 兜底（2026-09-29 第一波）：
 *
 * 现象：侧边栏导航切换 / 创建任务后主内容区空白无内容（刷新恢复）——前端 bundle
 * 渲染时序问题，渲染异常时无 ErrorBoundary 兜底 → React 抛错 → 整个 root 空白。
 *
 * 本组件作用：
 * 1. 渲染异常时显示可见兜底 UI（白屏变可见错误），不再无痕空白；
 * 2. 上报 POST /api/v1/client-error（与 server.js 注入的 error-reporter 同通道，
 *    adapter 写 .client-errors.jsonl → AI tail 可定位）；
 * 3. 挂点：main.tsx 根级（label="root"）+ AppShell 路由出口 <Outlet />（label="route"，
 *    配合 key={location.pathname} 实现切页自动重置，无需刷新即可恢复）。
 */
function reportClientError(payload: Record<string, unknown>) {
  try {
    const body = JSON.stringify({
      type: "errorboundary",
      ts: Date.now(),
      href: window.location.href,
      ua: navigator.userAgent,
      ...payload,
    });
    if (typeof navigator.sendBeacon === "function") {
      navigator.sendBeacon("/api/v1/client-error", body);
    } else {
      void fetch("/api/v1/client-error", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
      }).catch(() => {});
    }
  } catch {
    // 上报失败不影响兜底 UI 渲染
  }
}

type ErrorBoundaryProps = {
  children: ReactNode;
  /** 兜底标识（上报/日志区分挂点：root / route） */
  label?: string;
  /** 重置键（如路由 pathname）：变化时自动清除兜底状态——替代 key remount（避免切页整树重挂的卡顿） */
  resetKey?: string;
};

type ErrorBoundaryState = {
  error: Error | null;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    const label = this.props.label ?? "";
    console.error(`[ErrorBoundary${label ? `:${label}` : ""}]`, error, info?.componentStack ?? "");
    reportClientError({
      label,
      message: error?.message ? String(error.message) : String(error),
      stack: error?.stack ?? "",
      componentStack: info?.componentStack ?? "",
    });
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    // resetKey 变化（如路由切换）且处于兜底态 → 自动重置（无需 key remount 即可切页恢复，且避免整树重挂）
    if (this.state.error !== null && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  render() {
    const { error } = this.state;
    if (error === null) {
      return this.props.children;
    }
    // 兜底 UI：纯内联样式 + 常用的主题类（不依赖业务布局/i18n——错误发生时它们本身可能已崩）
    return (
      <div className="grid min-h-64 place-items-center p-6" role="alert">
        <div
          className="grid max-w-xl gap-3 rounded-lg border border-border bg-background p-6 text-foreground"
          style={{ borderColor: "rgba(220,38,38,0.45)" }}
        >
          <h1 className="text-lg font-bold" style={{ margin: 0 }}>
            页面渲染出错 · Page failed to render
          </h1>
          <p className="text-sm" style={{ margin: 0, color: "rgba(128,128,128,1)" }}>
            该错误已自动上报。刷新页面通常可恢复；若反复出现请反馈页面地址。
            This error was reported automatically — a reload usually restores the page.
          </p>
          <pre
            className="max-h-40 overflow-auto rounded-lg border border-border p-3 text-xs font-mono"
            style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}
          >
            {error?.message ? String(error.message) : String(error)}
          </pre>
          <div className="flex flex-wrap gap-2" style={{ margin: 0 }}>
            <button
              className="rounded-lg px-4 py-2 text-sm font-semibold text-background"
              style={{ background: "rgba(30,64,175,1)", color: "#fff" }}
              type="button"
              onClick={() => window.location.reload()}
            >
              刷新页面 · Reload
            </button>
            <button
              className="rounded-lg border border-border px-4 py-2 text-sm font-semibold"
              style={{ background: "rgba(239,239,239,1)" }}
              type="button"
              onClick={() => this.setState({ error: null })}
            >
              重试渲染 · Retry
            </button>
          </div>
        </div>
      </div>
    );
  }
}