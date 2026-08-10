import { Button, toast } from "@heroui/react";
import {
  IconCheck as Check,
  IconCloud as Cloud,
  IconFingerprint as Fingerprint,
  IconLink as Link,
  IconNotes as Notes,
  IconPower as Power,
  IconUserPlus as UserPlus,
  IconX as X,
} from "@tabler/icons-react";
import { useId, useState, type FormEvent } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";

import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { parsePawchiveCreatorUrl } from "../lib/pawchive";
import { useRealtime } from "../lib/realtime";
import type { CreatorReference, CreatorSummary } from "../types";
import { ExternalChangeAlert } from "./ExternalChangeAlert";
import {
  AddressText,
  FormField,
  FormModal,
  FormSwitchField,
  InlineCode,
  PawchiveIdentityFields,
  SelectField,
} from "./ui";

export type CreatorEditorRequest =
  | { kind: "create"; prefill?: CreatorSummary }
  | { kind: "edit"; creator: CreatorReference };

export function CreatorEditorModal({
  request,
  temporary = false,
  onClose,
  onSaved,
}: {
  request: CreatorEditorRequest;
  temporary?: boolean;
  onClose: () => void;
  onSaved?: (creator: CreatorReference) => void | Promise<void>;
}) {
  const { t } = useTranslation();
  const auth = useAuth(false);
  const session = auth?.session;
  const queryClient = useQueryClient();
  const realtime = useRealtime(false);
  const formId = `creator-editor-${useId().replaceAll(":", "")}`;
  const original = request.kind === "edit" ? request.creator : undefined;
  const prefill = request.kind === "create" ? request.prefill : undefined;
  const initial: CreatorReference = original
    ? { ...original }
    : prefill
      ? { service: prefill.service, creator_id: prefill.id, alias: null, enabled: true }
      : { service: "fanbox", creator_id: "", alias: null, enabled: true };
  const [editor, setEditor] = useState<CreatorReference>(initial);
  const [editorOriginal] = useState<CreatorReference>(initial);
  const [identityMode, setIdentityMode] = useState<"url" | "fields">(
    original || prefill ? "fields" : "url",
  );
  const [creatorUrl, setCreatorUrl] = useState("");
  const [creatorUrlError, setCreatorUrlError] = useState<string>();
  const [saving, setSaving] = useState(false);
  const [editorRevisionBaseline, setEditorRevisionBaseline] = useState(
    realtime?.revisions.creators ?? 0,
  );
  const originalKey = original ? `${original.service}/${original.creator_id}` : null;
  const creatorRevision = realtime?.revisions.creators ?? 0;

  async function saveCreator(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    let creator = editor;
    if (!originalKey && identityMode === "url") {
      const identity = parsePawchiveCreatorUrl(creatorUrl);
      if (!identity) {
        setCreatorUrlError(t("creators.creatorUrlInvalid"));
        return;
      }
      creator = {
        ...editor,
        service: identity.service,
        creator_id: identity.creatorId,
      };
    }

    setSaving(true);
    try {
      if (temporary) {
        await onSaved?.({ ...creator, enabled: true });
      } else {
        if (!session) return;
        const saved = originalKey
          ? await api<CreatorReference>(`/creators/${originalKey}`, {
              method: "PUT",
              body: { alias: creator.alias || null, enabled: creator.enabled },
              csrfToken: session.csrf_token,
            })
          : await api<CreatorReference>("/creators", {
              method: "POST",
              body: creator,
              csrfToken: session.csrf_token,
            });
        toast.success(originalKey ? t("creators.updated") : t("creators.added"));
        await queryClient.invalidateQueries({ queryKey: ["creators"] });
        await onSaved?.(saved);
      }
      onClose();
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSaving(false);
    }
  }

  return (
    <FormModal
      actions={
        <>
          <Button variant="ghost" onPress={onClose}>
            <X aria-hidden="true" size={17} />
            {t("common.cancel")}
          </Button>
          <Button form={formId} isPending={saving} type="submit" variant="primary">
            {temporary ? (
              <UserPlus aria-hidden="true" size={17} />
            ) : (
              <Check aria-hidden="true" size={17} />
            )}
            {temporary ? t("tasks.addTemporaryCreatorAction") : t("common.save")}
          </Button>
        </>
      }
      open
      title={
        temporary
          ? t("tasks.addTemporaryCreator")
          : originalKey
            ? t("creators.edit")
            : t("creators.add")
      }
      onOpenChange={(open) => !open && onClose()}
    >
      <form className="grid gap-5" id={formId} onSubmit={saveCreator}>
        {temporary ? (
          <p className="text-sm leading-relaxed text-muted">{t("tasks.temporaryCreatorModalHint")}</p>
        ) : null}
        <ExternalChangeAlert
          visible={Boolean(
            originalKey &&
              JSON.stringify(editor) !== JSON.stringify(editorOriginal) &&
              creatorRevision > editorRevisionBaseline
          )}
          onKeepEditing={() => setEditorRevisionBaseline(creatorRevision)}
          onReload={onClose}
        />
        {!originalKey ? (
          <SelectField
            description={t("creators.identityModeHint")}
            icon={Fingerprint}
            label={t("creators.identityMode")}
            options={[
              { value: "url", label: t("creators.identityUrl"), icon: Link },
              { value: "fields", label: t("creators.identityFields"), icon: Fingerprint },
            ]}
            value={identityMode}
            onChange={(value) => {
              setCreatorUrlError(undefined);
              setIdentityMode(value === "fields" ? "fields" : "url");
            }}
          />
        ) : null}
        {!originalKey && identityMode === "url" ? (
          <FormField
            description={<AddressText text={t("creators.creatorUrlHint")} />}
            errorMessage={creatorUrlError}
            icon={Link}
            inputClassName="font-mono text-[0.8125rem]"
            isInvalid={Boolean(creatorUrlError)}
            isRequired
            label={t("creators.creatorUrl")}
            value={creatorUrl}
            onChange={(value) => {
              setCreatorUrl(value);
              setCreatorUrlError(undefined);
            }}
          />
        ) : (
          <PawchiveIdentityFields
            creatorId={editor.creator_id}
            creatorIdLabel={t("creators.creatorId")}
            description={
              originalKey ? (
                t("creators.identityLockedHint")
              ) : (
                <Trans
                  components={{ code: <InlineCode /> }}
                  i18nKey="creators.identityHint"
                />
              )
            }
            icon={Cloud}
            isReadOnly={Boolean(originalKey)}
            label={t("creators.identity")}
            service={editor.service}
            serviceLabel={t("creators.service")}
            onCreatorIdChange={(creator_id) => setEditor({ ...editor, creator_id })}
            onServiceChange={(service) => setEditor({ ...editor, service })}
          />
        )}
        <FormField
          description={temporary ? t("tasks.temporaryCreatorAliasHint") : t("creators.aliasHint")}
          icon={Notes}
          label={t("creators.alias")}
          value={editor.alias ?? ""}
          onChange={(alias) => setEditor({ ...editor, alias: alias || null })}
        />
        {!temporary ? (
          <FormSwitchField
            description={t("creators.enabledHint")}
            icon={Power}
            isSelected={editor.enabled}
            label={t("creators.enabled")}
            onChange={(enabled) => setEditor({ ...editor, enabled })}
          />
        ) : null}
      </form>
    </FormModal>
  );
}
