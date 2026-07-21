import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

type ThemeMode = "light" | "dark" | "system";
type EffectiveTheme = "light" | "dark";

type ThemeContextValue = {
  mode: ThemeMode;
  effective: EffectiveTheme;
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function systemTheme(): EffectiveTheme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const stored = localStorage.getItem("ktoolbox-theme") as ThemeMode | null;
  const [mode, setModeState] = useState<ThemeMode>(stored ?? "system");
  const [system, setSystem] = useState<EffectiveTheme>(systemTheme);
  const effective = mode === "system" ? system : mode;

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setSystem(media.matches ? "dark" : "light");
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = effective;
    document.documentElement.style.colorScheme = effective;
  }, [effective]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      mode,
      effective,
      setMode: (next) => {
        setModeState(next);
        localStorage.setItem("ktoolbox-theme", next);
      },
      toggle: () => {
        const next = effective === "dark" ? "light" : "dark";
        setModeState(next);
        localStorage.setItem("ktoolbox-theme", next);
      },
    }),
    [effective, mode],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useTheme must be used inside ThemeProvider");
  return value;
}
