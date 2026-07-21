import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, ApiError } from "./api";
import type { Session } from "../types";

type AuthContextValue = {
  session: Session | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api<Session>("/session")
      .then((value) => {
        if (active) setSession(value);
      })
      .catch((error: unknown) => {
        if (!(error instanceof ApiError && error.status === 401)) throw error;
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      loading,
      login: async (username, password) => {
        const next = await api<Session>("/session/login", {
          method: "POST",
          body: { username, password },
        });
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        setSession(next);
      },
      logout: async () => {
        if (session) {
          await api<void>("/session/logout", {
            method: "POST",
            csrfToken: session.csrf_token,
          });
        }
        setSession(null);
      },
    }),
    [loading, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
