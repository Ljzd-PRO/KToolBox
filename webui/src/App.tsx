import { Spinner, ToastProvider } from "@heroui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { AuthProvider, useAuth } from "./lib/auth";
import { ThemeProvider } from "./lib/theme";
import { DashboardPage } from "./pages/DashboardPage";
import { BlockersPage } from "./pages/BlockersPage";
import { CreatorsPage } from "./pages/CreatorsPage";
import { ConfigurationPage } from "./pages/ConfigurationPage";
import { LoginPage } from "./pages/LoginPage";
import { PostsPage } from "./pages/PostsPage";
import { SystemPage } from "./pages/SystemPage";
import { TasksPage } from "./pages/TasksPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 10_000 },
  },
});

function AuthenticatedApplication() {
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <main className="grid min-h-dvh place-items-center bg-background text-foreground">
        <Spinner aria-label="Loading session" size="lg" />
      </main>
    );
  }
  if (!session) {
    return (
      <>
        <LoginPage />
        <ToastProvider placement="top" width={360} />
      </>
    );
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
        <Route element={<SystemPage />} path="system" />
        <Route element={<Navigate replace to="/" />} path="*" />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AuthenticatedApplication />
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
