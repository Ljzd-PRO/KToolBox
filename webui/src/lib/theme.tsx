import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

type ThemeMode = "light" | "dark" | "system";
type EffectiveTheme = "light" | "dark";
export type ThemeColor = "blue" | "emerald" | "violet" | "rose" | "amber";

type ThemeContextValue = {
  mode: ThemeMode;
  effective: EffectiveTheme;
  color: ThemeColor;
  setMode: (mode: ThemeMode) => void;
  setColor: (color: ThemeColor) => void;
  toggle: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function systemTheme(): EffectiveTheme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const stored = localStorage.getItem("ktoolbox-theme") as ThemeMode | null;
  const storedColor = localStorage.getItem("ktoolbox-theme-color") as ThemeColor | null;
  const [mode, setModeState] = useState<ThemeMode>(stored ?? "system");
  const [color, setColorState] = useState<ThemeColor>(storedColor ?? "blue");
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
    document.documentElement.dataset.colorScheme = effective;
    document.documentElement.dataset.themeColor = color;
    document.documentElement.style.colorScheme = effective;
  }, [color, effective]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      mode,
      effective,
      color,
      setMode: (next) => {
        setModeState(next);
        localStorage.setItem("ktoolbox-theme", next);
      },
      setColor: (next) => {
        setColorState(next);
        localStorage.setItem("ktoolbox-theme-color", next);
      },
      toggle: () => {
        const next = effective === "dark" ? "light" : "dark";
        setModeState(next);
        localStorage.setItem("ktoolbox-theme", next);
      },
    }),
    [color, effective, mode],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useTheme must be used inside ThemeProvider");
  return value;
}
