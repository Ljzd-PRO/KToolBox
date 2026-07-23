import { Spinner, ToastProvider } from "@heroui/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { I18nProvider } from "react-aria-components";
import { Navigate, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { AppShell } from "./components/AppShell";
import { AuthProvider, useAuth } from "./lib/auth";
import { normalizeLanguage, reactAriaLocale } from "./lib/i18n";
import { queryClient } from "./lib/query";
import { ThemeProvider } from "./lib/theme";
import { DashboardPage } from "./pages/DashboardPage";
import { BlockersPage } from "./pages/BlockersPage";
import { CreatorsPage } from "./pages/CreatorsPage";
import { ConfigurationPage } from "./pages/ConfigurationPage";
import { LoginPage } from "./pages/LoginPage";
import { MCPPage } from "./pages/MCPPage";
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
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route element={<TasksPage />} path="tasks/:taskId?" />
        <Route element={<CreatorsPage />} path="creators" />
        <Route element={<PostsPage />} path="posts" />
        <Route element={<BlockersPage />} path="blockers" />
        <Route element={<ConfigurationPage />} path="configuration" />
        <Route element={<MCPPage />} path="mcp" />
        <Route element={<SystemPage />} path="system" />
        <Route element={<Navigate replace to="/" />} path="*" />
      </Route>
    </Routes>
  );
}

export function App() {
  const { i18n } = useTranslation();
  const locale = reactAriaLocale(normalizeLanguage(i18n.resolvedLanguage ?? i18n.language));
  return (
    <I18nProvider locale={locale}>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AuthenticatedApplication />
            <ToastProvider placement="top" width={360} />
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </I18nProvider>
  );
}
