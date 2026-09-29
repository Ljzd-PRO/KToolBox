import { lazy, Suspense } from "react";
import { Spinner, Toast } from "@heroui/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { I18nProvider } from "react-aria-components";
import { Navigate, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { AppShell } from "./components/AppShell";
import { StartupNoticeCenter } from "./components/StartupNoticeCenter";
import { AuthProvider, useAuth } from "./lib/auth";
import { normalizeLanguage, reactAriaLocale } from "./lib/i18n";
import { queryClient } from "./lib/query";
import { RealtimeProvider } from "./lib/realtime";
import { SensitiveMediaProvider } from "./lib/sensitiveMedia";
import { ThemeProvider } from "./lib/theme";
// 首屏相关（登录页/首页）保持静态——冷启动只加载核心 chunk
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
// 非首屏路由懒加载（2026-09-29 首屏性能优化——冷启动不再全量加载全部页面组件）
const TasksPage = lazy(() => import("./pages/TasksPage").then((m) => ({ default: m.TasksPage })));
const AutomaticSyncPage = lazy(() => import("./pages/AutomaticSyncPage").then((m) => ({ default: m.AutomaticSyncPage })));
const CreatorsPage = lazy(() => import("./pages/CreatorsPage").then((m) => ({ default: m.CreatorsPage })));
const PostsPage = lazy(() => import("./pages/PostsPage").then((m) => ({ default: m.PostsPage })));
const BlockersPage = lazy(() => import("./pages/BlockersPage").then((m) => ({ default: m.BlockersPage })));
const ConfigurationPage = lazy(() => import("./pages/ConfigurationPage").then((m) => ({ default: m.ConfigurationPage })));
const NamingPage = lazy(() => import("./pages/NamingPage").then((m) => ({ default: m.NamingPage })));
const MCPPage = lazy(() => import("./pages/MCPPage").then((m) => ({ default: m.MCPPage })));
const SystemPage = lazy(() => import("./pages/SystemPage").then((m) => ({ default: m.SystemPage })));
const AboutPage = lazy(() => import("./pages/AboutPage").then((m) => ({ default: m.AboutPage })));

function AuthenticatedApplication() {
  const { t } = useTranslation();
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <main className="grid min-h-dvh place-items-center bg-background text-foreground">
        <Spinner aria-label={t("common.loading")} size="lg" />
      </main>
    );
  }
  if (!session) {
    return <LoginPage />;
  }
  return (
    <RealtimeProvider>
      <SensitiveMediaProvider>
        <Suspense fallback={(
          <main className="grid min-h-dvh place-items-center bg-background text-foreground">
            <Spinner aria-label={t("common.loading")} size="lg" />
          </main>
        )}>
          <Routes>
            <Route element={<AppShell />}>
              <Route index element={<DashboardPage />} />
              <Route element={<TasksPage />} path="tasks/:taskId?" />
              <Route element={<AutomaticSyncPage />} path="auto-sync" />
              <Route element={<CreatorsPage />} path="creators" />
              <Route element={<PostsPage />} path="posts" />
              <Route element={<BlockersPage />} path="blockers" />
              <Route element={<ConfigurationPage />} path="setting" />
              <Route element={<Navigate replace to="/setting" />} path="configuration" />
              <Route element={<NamingPage />} path="naming" />
              <Route element={<MCPPage />} path="mcp" />
              <Route element={<SystemPage />} path="system" />
              <Route element={<AboutPage />} path="about" />
              <Route element={<Navigate replace to="/" />} path="*" />
            </Route>
          </Routes>
        </Suspense>
        <StartupNoticeCenter />
      </SensitiveMediaProvider>
    </RealtimeProvider>
  );
}

export function App() {
  const { i18n, t } = useTranslation();
  const locale = reactAriaLocale(normalizeLanguage(i18n.resolvedLanguage ?? i18n.language));
  return (
    <I18nProvider locale={locale}>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AuthenticatedApplication />
            <Toast.Provider placement="top" width={360}>
              {({ toast: item }) => {
                const content = item.content;
                return (
                  <Toast
                    placement="top"
                    scaleFactor={0.05}
                    toast={item}
                    variant={content.variant}
                  >
                    {content.indicator === null ? null : content.isLoading ? (
                      <Toast.Indicator variant={content.variant}>
                        <Spinner color="current" size="sm" />
                      </Toast.Indicator>
                    ) : (
                      <Toast.Indicator variant={content.variant}>
                        {content.indicator}
                      </Toast.Indicator>
                    )}
                    <Toast.Content>
                      {content.title ? <Toast.Title>{content.title}</Toast.Title> : null}
                      {content.description ? (
                        <Toast.Description>{content.description}</Toast.Description>
                      ) : null}
                    </Toast.Content>
                    {content.actionProps?.children ? (
                      <Toast.ActionButton {...content.actionProps}>
                        {content.actionProps.children}
                      </Toast.ActionButton>
                    ) : null}
                    <Toast.CloseButton aria-label={t("common.close")} />
                  </Toast>
                );
              }}
            </Toast.Provider>
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </I18nProvider>
  );
}
