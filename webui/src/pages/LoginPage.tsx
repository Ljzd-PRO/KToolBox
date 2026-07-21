import { Alert, Button, Surface, toast } from "@heroui/react";
import { LockKeyhole, LogIn, ShieldAlert } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { FormField, PasswordField } from "../components/ui";
import { errorText } from "../lib/api";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

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
        <header className="flex items-center gap-3">
          <span className="brand-mark grid size-10 place-items-center rounded-lg" aria-hidden="true">
            <LockKeyhole size={20} strokeWidth={2} />
          </span>
          <div>
            <div className="text-lg font-semibold">{t("brand")}</div>
            <div className="text-xs text-muted">{t("subtitle")}</div>
          </div>
        </header>

        <Surface className="mx-auto w-full max-w-md rounded-lg border border-border p-6 shadow-sm sm:p-8">
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
              isRequired
              label={t("login.username")}
              value={username}
              onChange={setUsername}
            />
            <PasswordField label={t("login.password")} value={password} onChange={setPassword} />
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
        </Surface>

        <p className="text-center text-xs text-muted">{t("subtitle")}</p>
      </div>
    </main>
  );
}
