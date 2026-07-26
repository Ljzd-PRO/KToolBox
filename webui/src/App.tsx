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
import { ThemeProvider } from "./lib/theme";
import { DashboardPage } from "./pages/DashboardPage";
import { AboutPage } from "./pages/AboutPage";
import { BlockersPage } from "./pages/BlockersPage";
import { CreatorsPage } from "./pages/CreatorsPage";
import { ConfigurationPage } from "./pages/ConfigurationPage";
import { LoginPage } from "./pages/LoginPage";
import { MCPPage } from "./pages/MCPPage";
import { NamingPage } from "./pages/NamingPage";
import { PostsPage } from "./pages/PostsPage";
import { SystemPage } from "./pages/SystemPage";
import { TasksPage } from "./pages/TasksPage";

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
      <>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route element={<TasksPage />} path="tasks/:taskId?" />
            <Route element={<CreatorsPage />} path="creators" />
            <Route element={<PostsPage />} path="posts" />
            <Route element={<BlockersPage />} path="blockers" />
            <Route element={<ConfigurationPage />} path="configuration" />
            <Route element={<NamingPage />} path="naming" />
            <Route element={<MCPPage />} path="mcp" />
            <Route element={<SystemPage />} path="system" />
            <Route element={<AboutPage />} path="about" />
            <Route element={<Navigate replace to="/" />} path="*" />
          </Route>
        </Routes>
        <StartupNoticeCenter />
      </>
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
