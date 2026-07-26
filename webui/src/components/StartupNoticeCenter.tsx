import { Alert, Button, toast } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconArchive as Archive,
  IconCheck as Check,
  IconFolderCog as FolderCog,
  IconTerminal2 as Terminal,
} from "@tabler/icons-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { StartupNotice } from "../types";
import { ConfirmModal, InlineCode } from "./ui";

function stringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export function StartupNoticeCenter() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [acknowledging, setAcknowledging] = useState(false);
  const [dismissedNoticeId, setDismissedNoticeId] = useState<string | null>(null);
  const notices = useQuery({
    queryKey: ["startup-notices"],
    queryFn: () => api<StartupNotice[]>("/startup-notices"),
  });
  const notice =
    notices.data?.find((item) => item.id !== dismissedNoticeId) ?? null;
  const backups = stringList(notice?.payload?.backup_paths);
  const ignoredEnvironment = stringList(notice?.payload?.ignored_environment_keys);

  async function acknowledge() {
    if (!notice || !session) return;
    setAcknowledging(true);
    try {
      await api<StartupNotice>(`/startup-notices/${notice.id}/acknowledge`, {
        method: "POST",
        csrfToken: session.csrf_token,
      });
      setDismissedNoticeId(notice.id);
      queryClient.setQueryData<StartupNotice[]>(
        ["startup-notices"],
        (current) => current?.filter((item) => item.id !== notice.id) ?? [],
      );
      toast.success(t("naming.migration.acknowledged"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setAcknowledging(false);
    }
  }

  return (
    <ConfirmModal
      open={notice !== null}
      title={t("naming.migration.title")}
      actions={
        <Button isPending={acknowledging} variant="primary" onPress={() => void acknowledge()}>
          <Check aria-hidden="true" size={17} />
          {t("naming.migration.acknowledge")}
        </Button>
      }
      onOpenChange={() => undefined}
    >
      <div className="grid gap-4">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent-soft-foreground">
            <FolderCog aria-hidden="true" size={20} stroke={1.8} />
          </span>
          <div className="min-w-0">
            <p className="font-semibold text-foreground">{t("naming.migration.complete")}</p>
            <p className="mt-1 text-sm leading-6 text-muted">{t("naming.migration.body")}</p>
          </div>
        </div>
        {backups.length ? (
          <section className="grid gap-2 rounded-lg border border-border bg-default p-3">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <Archive aria-hidden="true" size={16} />
              {t("naming.migration.backups")}
            </h3>
            <div className="grid gap-1.5">
              {backups.map((path) => (
                <InlineCode className="block min-w-0 break-all" key={path}>
                  {path}
                </InlineCode>
              ))}
            </div>
          </section>
        ) : null}
        {ignoredEnvironment.length ? (
          <Alert status="warning">
            <Alert.Indicator>
              <Terminal aria-hidden="true" size={17} />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Title className="flex items-center gap-2">
                <Terminal aria-hidden="true" size={16} />
                {t("naming.migration.environmentTitle")}
              </Alert.Title>
              <Alert.Description>
                {t("naming.migration.environmentBody")}
                <span className="mt-2 flex flex-wrap gap-1.5">
                  {ignoredEnvironment.map((name) => (
                    <InlineCode key={name}>{name}</InlineCode>
                  ))}
                </span>
              </Alert.Description>
            </Alert.Content>
          </Alert>
        ) : null}
      </div>
    </ConfirmModal>
  );
}
