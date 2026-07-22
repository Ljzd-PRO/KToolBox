import { Alert, Button, toast } from "@heroui/react";
import {
  IconKey as KeyRound,
  IconLock as LockKeyhole,
  IconLogin as LogIn,
  IconMoon,
  IconShieldExclamation as ShieldAlert,
  IconSun,
  IconUser as UserRound,
} from "@tabler/icons-react";
import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { FormField, FormSurface, IconButton, PasswordField } from "../components/ui";
import { LanguageSelector } from "../components/LanguageSelector";
import { errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useTheme } from "../lib/theme";

export function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const theme = useTheme();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    document.title = `${t("login.title")} - ${t("brand")}`;
  }, [t]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await login(username, password);
    } catch (error) {
      toast.danger(t("login.failed"), { description: errorText(error) });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-screen min-h-dvh bg-background px-4 py-8 text-foreground sm:px-8">
      <div className="mx-auto flex min-h-[calc(100dvh-4rem)] max-w-6xl flex-col justify-between gap-8">
        <header className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span className="brand-mark grid size-10 shrink-0 place-items-center rounded-lg" aria-hidden="true">
              <LockKeyhole size={20} strokeWidth={2} />
            </span>
            <div className="min-w-0">
              <div className="truncate text-lg font-semibold">{t("brand")}</div>
              <div className="truncate text-xs text-muted">{t("subtitle")}</div>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <IconButton
              icon={theme.effective === "dark" ? IconSun : IconMoon}
              label={theme.effective === "dark" ? t("shell.themeLight") : t("shell.themeDark")}
              onPress={theme.toggle}
            />
            <LanguageSelector />
          </div>
        </header>

        <FormSurface className="mx-auto w-full max-w-md p-6 sm:p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold">{t("login.title")}</h1>
            <p className="mt-2 text-sm leading-relaxed text-muted">{t("login.description")}</p>
          </div>
          <Alert status="warning" className="mb-6 rounded-lg">
            <Alert.Indicator>
              <ShieldAlert aria-hidden="true" size={18} />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Title>{t("shell.securityTitle")}</Alert.Title>
              <Alert.Description>{t("shell.securityBody")}</Alert.Description>
            </Alert.Content>
          </Alert>
          <form aria-busy={submitting} className="grid gap-5" onSubmit={submit}>
            <FormField
              autoComplete="username"
              icon={UserRound}
              isRequired
              label={t("login.username")}
              value={username}
              onChange={setUsername}
            />
            <PasswordField icon={KeyRound} isRequired label={t("login.password")} value={password} onChange={setPassword} />
            <Button
              className="mt-1 w-full"
              isDisabled={submitting}
              type="submit"
              variant="primary"
            >
              <LogIn aria-hidden="true" size={18} />
              {submitting ? t("login.signingIn") : t("login.submit")}
            </Button>
          </form>
        </FormSurface>

        <p className="text-center text-xs text-muted">{t("subtitle")}</p>
      </div>
    </main>
  );
}
