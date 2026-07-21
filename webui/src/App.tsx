import { Spinner, ToastProvider } from "@heroui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { AuthProvider, useAuth } from "./lib/auth";
import { ThemeProvider } from "./lib/theme";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { SystemPage } from "./pages/SystemPage";

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
        <Route element={<PlaceholderPage page="tasks" />} path="tasks/*" />
        <Route element={<PlaceholderPage page="creators" />} path="creators" />
        <Route element={<PlaceholderPage page="posts" />} path="posts" />
        <Route element={<PlaceholderPage page="blockers" />} path="blockers" />
        <Route element={<PlaceholderPage page="configuration" />} path="configuration" />
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
