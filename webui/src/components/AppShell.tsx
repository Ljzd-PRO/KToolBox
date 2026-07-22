import { Button, Drawer, Popover, Surface, Tooltip, toast, useOverlayState } from "@heroui/react";
import {
  IconAdjustmentsHorizontal,
  IconAddressBook,
  IconBan,
  IconDeviceDesktop,
  IconFileSearch,
  IconGauge,
  IconLogout,
  IconMenu2,
  IconMoon,
  IconPackages,
  IconPalette,
  IconSettingsCog,
  IconShieldLock,
  IconSun,
  IconTool,
  IconX,
  type TablerIcon,
} from "@tabler/icons-react";
import { useEffect } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useTheme, type ThemeColor } from "../lib/theme";
import { LanguageSelector } from "./LanguageSelector";
import { IconButton } from "./ui";

type NavigationItem = {
  key: string;
  path: string;
  icon: TablerIcon;
};

const navigation: NavigationItem[] = [
  { key: "overview", path: "/", icon: IconGauge },
  { key: "tasks", path: "/tasks", icon: IconPackages },
  { key: "creators", path: "/creators", icon: IconAddressBook },
  { key: "posts", path: "/posts", icon: IconFileSearch },
  { key: "blockers", path: "/blockers", icon: IconBan },
  { key: "configuration", path: "/configuration", icon: IconSettingsCog },
  { key: "system", path: "/system", icon: IconAdjustmentsHorizontal },
];

const themeColors: ThemeColor[] = ["blue", "emerald", "violet", "rose", "amber"];

function Navigation({ onSelect }: { onSelect?: () => void }) {
  const { t } = useTranslation();
  return (
    <nav aria-label={t("shell.primaryNavigation")} className="grid gap-1">
      {navigation.map(({ key, path, icon: Icon }) => (
        <NavLink
          className={({ isActive }) =>
            `nav-link relative flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-semibold ${isActive ? "nav-link-active" : ""}`
          }
          end={path === "/"}
          key={key}
          to={path}
          onClick={onSelect}
        >
          <Icon aria-hidden="true" className="shrink-0" size={19} stroke={1.8} />
          <span className="truncate">{t(`nav.${key}`)}</span>
        </NavLink>
      ))}
    </nav>
  );
}

function Brand({ version }: { version?: string }) {
  const { t } = useTranslation();
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="brand-mark grid size-16 shrink-0 place-items-center rounded-lg" aria-hidden="true">
        <IconTool size={30} stroke={1.8} />
      </span>
      <div className="grid min-w-0 gap-0.5">
        <div className="truncate text-lg font-bold leading-tight text-foreground">{t("brand")}</div>
        <div className="truncate text-xs font-medium text-muted">{t("subtitle")}</div>
        {version ? (
          <span className="mt-0.5 w-fit rounded-md bg-default px-1.5 py-0.5 text-[0.6875rem] font-semibold leading-none text-muted">
            v{version}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function ThemeControls({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();
  const theme = useTheme();
  const modes = [
    { value: "system" as const, icon: IconDeviceDesktop, label: t("shell.themeSystem") },
    { value: "light" as const, icon: IconSun, label: t("shell.themeLight") },
    { value: "dark" as const, icon: IconMoon, label: t("shell.themeDark") },
  ];
  return (
    <Surface
      aria-label={t("shell.theme")}
      className={`theme-control min-h-11 rounded-lg ${compact ? "grid w-full justify-items-center gap-1 p-2" : "flex items-center gap-1 p-1"}`}
      role="group"
    >
      <div className="flex items-center gap-1">
        <IconPalette aria-hidden="true" className="mx-1 shrink-0 text-muted" size={16} stroke={1.8} />
        {themeColors.map((color) => {
          const label = t(`shell.themeColors.${color}`);
          return (
            <Tooltip key={color}>
              <Button
                isIconOnly
                aria-label={label}
                aria-pressed={theme.color === color}
                className="h-8 w-8 min-w-8 rounded-lg"
                size="sm"
                variant="ghost"
                onPress={() => theme.setColor(color)}
              >
                <span
                  aria-hidden="true"
                  className="theme-swatch size-3.5 rounded-full"
                  data-color={color}
                  data-selected={theme.color === color}
                />
              </Button>
              <Tooltip.Content>{label}</Tooltip.Content>
            </Tooltip>
          );
        })}
      </div>
      <span aria-hidden="true" className={compact ? "h-px w-full bg-border" : "mx-1 h-6 w-px bg-border"} />
      <div className="flex items-center gap-1">
        {modes.map(({ value, icon: Icon, label }) => (
          <Tooltip key={value}>
            <Button
              isIconOnly
              aria-label={label}
              aria-pressed={theme.mode === value}
              className="h-8 w-8 min-w-8 rounded-lg"
              size="sm"
              variant={theme.mode === value ? "secondary" : "ghost"}
              onPress={() => theme.setMode(value)}
            >
              <Icon aria-hidden="true" size={16} stroke={1.8} />
            </Button>
            <Tooltip.Content>{label}</Tooltip.Content>
          </Tooltip>
        ))}
      </div>
    </Surface>
  );
}

function SecurityNotice({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();

  return (
    <Popover>
      <Button
        isIconOnly={compact}
        aria-label={compact ? t("shell.securityTitle") : undefined}
        className={compact ? "size-11 min-w-11 shrink-0" : "h-11 max-w-56 justify-start"}
        variant="outline"
      >
        <IconShieldLock
          aria-hidden="true"
          className="shrink-0 text-[var(--ktoolbox-yellow)]"
          size={compact ? 18 : 17}
          stroke={1.8}
        />
        {compact ? null : <span className="truncate">{t("shell.securityTitle")}</span>}
      </Button>
      <Popover.Content
        className="w-80 max-w-[calc(100vw-2rem)] rounded-lg border border-border"
        offset={10}
        placement="bottom end"
      >
        <Popover.Arrow />
        <Popover.Dialog className="flex items-start gap-3 p-4">
          <span
            aria-hidden="true"
            className="grid size-9 shrink-0 place-items-center rounded-lg bg-warning-soft text-warning-soft-foreground"
          >
            <IconShieldLock size={18} stroke={1.8} />
          </span>
          <div className="grid min-w-0 gap-1.5">
            <Popover.Heading className="text-sm font-semibold text-foreground">
              {t("shell.securityTitle")}
            </Popover.Heading>
            <p className="text-sm leading-relaxed text-muted">{t("shell.securityBody")}</p>
            <p className="text-sm leading-relaxed text-foreground">{t("shell.securityAdvice")}</p>
          </div>
        </Popover.Dialog>
      </Popover.Content>
    </Popover>
  );
}

export function AppShell() {
  const { t } = useTranslation();
  const { session, logout } = useAuth();
  const theme = useTheme();
  const drawer = useOverlayState();
  const location = useLocation();
  const active =
    navigation.find((item) =>
      item.path === "/" ? location.pathname === "/" : location.pathname.startsWith(item.path),
    ) ?? navigation[0];
  const ActiveIcon = active.icon;

  useEffect(() => {
    document.title = `${t(`nav.${active.key}`)} - ${t("brand")}`;
  }, [active.key, t]);

  async function signOut() {
    try {
      await logout();
    } catch (error) {
      toast.danger(t("shell.logout"), { description: errorText(error) });
    }
  }

  return (
    <div className="min-h-dvh bg-background text-foreground md:grid md:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="sidebar hidden min-h-dvh border-r border-border md:sticky md:top-0 md:flex md:h-dvh md:flex-col">
        <div className="px-5 py-5">
          <Brand />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-2">
          <Navigation />
        </div>
        <div className="grid gap-2 border-t border-border px-4 py-4">
          <div className="flex min-w-0 items-center gap-2 px-2 text-xs font-medium text-muted">
            <IconShieldLock aria-hidden="true" className="shrink-0 text-[var(--ktoolbox-teal)]" size={16} stroke={1.8} />
            <span className="truncate">{session?.username}</span>
          </div>
          <Button className="w-full justify-start" variant="ghost" onPress={signOut}>
            <IconLogout aria-hidden="true" size={18} stroke={1.8} />
            {t("shell.logout")}
          </Button>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="shell-workbar sticky top-0 z-30 border-b border-border">
          <div className="mx-auto flex min-h-20 w-full max-w-7xl items-center gap-3 px-4 pl-20 sm:px-6 sm:pl-20 md:px-8 md:pl-8">
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-[var(--accent-strong)]">{t("brand")}</p>
              <h1 className="mt-1 flex min-w-0 items-center gap-2 text-xl font-bold leading-tight text-foreground sm:text-2xl max-[420px]:gap-0">
                <span className="page-title-icon grid size-9 shrink-0 place-items-center rounded-lg max-[420px]:hidden">
                  <ActiveIcon aria-hidden="true" size={21} stroke={1.8} />
                </span>
                <span className="min-w-0 break-words">{t(`nav.${active.key}`)}</span>
              </h1>
            </div>
            <div className="hidden min-w-0 items-center gap-2 xl:flex">
              <ThemeControls />
              <SecurityNotice />
            </div>
            <div className="xl:hidden">
              <SecurityNotice compact />
            </div>
            <LanguageSelector />
            <div className="hidden sm:block xl:hidden">
              <IconButton
                icon={theme.effective === "dark" ? IconSun : IconMoon}
                label={theme.effective === "dark" ? t("shell.themeLight") : t("shell.themeDark")}
                onPress={theme.toggle}
              />
            </div>
          </div>
        </header>

        <main className="mx-auto grid min-w-0 w-full max-w-7xl gap-5 p-4 sm:p-6 md:p-8">
          <Outlet />
        </main>
      </div>

      <Drawer state={drawer}>
        <Drawer.Trigger
          aria-label={t("shell.menu")}
          className="mobile-menu-button fixed left-4 top-[calc(env(safe-area-inset-top)+1rem)] z-40 grid size-12 min-w-12 place-items-center rounded-full p-0 leading-none md:hidden"
        >
          <IconMenu2 aria-hidden="true" size={22} stroke={1.9} />
        </Drawer.Trigger>
        <Drawer.Backdrop variant="blur">
          <Drawer.Content placement="left">
            <Drawer.Dialog className="w-[82vw] max-w-80 p-0">
              <Drawer.Header className="border-b border-border px-4 py-4">
                <div className="flex items-center justify-between gap-3">
                  <Drawer.Heading className="text-base font-semibold text-foreground">{t("shell.navigation")}</Drawer.Heading>
                  <Drawer.CloseTrigger
                    aria-label={t("shell.closeMenu")}
                    className="grid size-10 place-items-center rounded-lg text-muted hover:bg-default"
                  >
                    <IconX aria-hidden="true" size={18} stroke={1.8} />
                  </Drawer.CloseTrigger>
                </div>
              </Drawer.Header>
              <Drawer.Body className="grid min-h-0 content-start gap-5 p-4">
                <Brand />
                <Navigation onSelect={drawer.close} />
              </Drawer.Body>
              <div className="grid gap-3 border-t border-border p-4">
                <ThemeControls compact />
                <LanguageSelector compact={false} />
                <div className="flex min-w-0 items-center gap-2 px-2 text-xs font-medium text-muted">
                  <IconShieldLock aria-hidden="true" className="shrink-0 text-[var(--ktoolbox-teal)]" size={16} stroke={1.8} />
                  <span className="truncate">{session?.username}</span>
                </div>
                <Button className="w-full justify-start" variant="ghost" onPress={signOut}>
                  <IconLogout aria-hidden="true" size={18} stroke={1.8} />
                  {t("shell.logout")}
                </Button>
              </div>
            </Drawer.Dialog>
          </Drawer.Content>
        </Drawer.Backdrop>
      </Drawer>
    </div>
  );
}
