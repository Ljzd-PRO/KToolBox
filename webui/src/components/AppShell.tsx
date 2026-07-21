import { Alert, Button, Drawer, ToastProvider, toast, useOverlayState } from "@heroui/react";
import {
  Ban,
  BookUser,
  Boxes,
  CircleGauge,
  FileCog,
  FileSearch,
  Languages,
  LogOut,
  Menu,
  Moon,
  Settings2,
  ShieldAlert,
  Sun,
  Wrench,
  X,
  type LucideIcon,
} from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toggleLanguage } from "../lib/i18n";
import { useTheme } from "../lib/theme";
import { IconButton } from "./ui";

type NavigationItem = {
  key: string;
  path: string;
  icon: LucideIcon;
};

const navigation: NavigationItem[] = [
  { key: "overview", path: "/", icon: CircleGauge },
  { key: "tasks", path: "/tasks", icon: Boxes },
  { key: "creators", path: "/creators", icon: BookUser },
  { key: "posts", path: "/posts", icon: FileSearch },
  { key: "blockers", path: "/blockers", icon: Ban },
  { key: "configuration", path: "/configuration", icon: FileCog },
  { key: "system", path: "/system", icon: Settings2 },
];

function Navigation({ onSelect }: { onSelect?: () => void }) {
  const { t } = useTranslation();
  return (
    <nav aria-label="Primary" className="grid gap-1">
      {navigation.map(({ key, path, icon: Icon }) => (
        <NavLink
          className={({ isActive }) =>
            `nav-link flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium ${isActive ? "nav-link-active" : ""}`
          }
          end={path === "/"}
          key={key}
          to={path}
          onClick={onSelect}
        >
          <Icon aria-hidden="true" size={18} strokeWidth={1.8} />
          <span>{t(`nav.${key}`)}</span>
        </NavLink>
      ))}
    </nav>
  );
}

function Brand() {
  const { t } = useTranslation();
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="brand-mark grid size-10 shrink-0 place-items-center rounded-lg" aria-hidden="true">
        <Wrench size={20} strokeWidth={2} />
      </span>
      <div className="min-w-0">
        <div className="truncate font-semibold text-foreground">{t("brand")}</div>
        <div className="truncate text-xs text-muted">{t("subtitle")}</div>
      </div>
    </div>
  );
}

export function AppShell() {
  const { t } = useTranslation();
  const { session, logout } = useAuth();
  const theme = useTheme();
  const drawer = useOverlayState();
  const location = useLocation();
  const active = navigation.find((item) => (item.path === "/" ? location.pathname === "/" : location.pathname.startsWith(item.path)));

  async function signOut() {
    try {
      await logout();
    } catch (error) {
      toast.danger(t("shell.logout"), { description: errorText(error) });
    }
  }

  return (
    <div className="min-h-dvh bg-background text-foreground lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="sidebar hidden min-h-dvh border-r border-border lg:sticky lg:top-0 lg:flex lg:h-dvh lg:flex-col">
        <div className="border-b border-border p-4">
          <Brand />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <Navigation />
        </div>
        <div className="border-t border-border p-3">
          <div className="mb-2 truncate px-3 text-xs font-medium text-muted">{session?.username}</div>
          <Button className="w-full justify-start" variant="ghost" onPress={signOut}>
            <LogOut aria-hidden="true" size={18} />
            {t("shell.logout")}
          </Button>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="app-header sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
          <div className="flex min-h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
            <div className="lg:hidden">
              <IconButton icon={Menu} label={t("shell.menu")} onPress={drawer.open} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-foreground">{t(`nav.${active?.key ?? "overview"}`)}</p>
              <p className="truncate text-xs text-muted">{session?.username}</p>
            </div>
            <IconButton icon={Languages} label={t("shell.language")} onPress={() => void toggleLanguage()} />
            <IconButton
              icon={theme.effective === "dark" ? Sun : Moon}
              label={theme.effective === "dark" ? t("shell.light") : t("shell.dark")}
              onPress={theme.toggle}
            />
            <div className="hidden sm:block">
              <IconButton icon={LogOut} label={t("shell.logout")} onPress={() => void signOut()} />
            </div>
          </div>
          <Alert className="security-strip rounded-none border-x-0 border-b-0 px-4 py-2 sm:px-6 lg:px-8" status="warning">
            <Alert.Indicator>
              <ShieldAlert aria-hidden="true" size={16} />
            </Alert.Indicator>
            <Alert.Content className="flex-row items-baseline gap-2">
              <Alert.Title className="text-xs">{t("shell.securityTitle")}</Alert.Title>
              <Alert.Description className="hidden text-xs sm:inline">{t("shell.securityBody")}</Alert.Description>
            </Alert.Content>
          </Alert>
        </header>

        <main className="mx-auto w-full max-w-[1520px] p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      <Drawer state={drawer}>
        <Drawer.Backdrop>
          <Drawer.Content placement="left">
            <Drawer.Dialog className="p-0">
              <Drawer.Header className="border-b border-border p-4">
                <div className="flex items-center justify-between gap-3">
                  <Brand />
                  <Drawer.CloseTrigger
                    aria-label={t("shell.closeMenu")}
                    className="grid size-11 place-items-center rounded-lg text-muted hover:bg-default"
                  >
                    <X aria-hidden="true" size={19} />
                  </Drawer.CloseTrigger>
                </div>
              </Drawer.Header>
              <Drawer.Body className="p-3">
                <Navigation onSelect={drawer.close} />
              </Drawer.Body>
              <div className="border-t border-border p-3">
                <Button className="w-full justify-start" variant="ghost" onPress={signOut}>
                  <LogOut aria-hidden="true" size={18} />
                  {t("shell.logout")}
                </Button>
              </div>
            </Drawer.Dialog>
          </Drawer.Content>
        </Drawer.Backdrop>
      </Drawer>
      <ToastProvider placement="top" width={360} />
    </div>
  );
}
