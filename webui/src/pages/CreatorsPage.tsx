import {
  Button,
  Chip,
  SearchField,
  Surface,
  Table,
  toast,
} from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconCheck as Check,
  IconCloud as Cloud,
  IconPencil as Pencil,
  IconPlus as Plus,
  IconPower as Power,
  IconSearch as Search,
  IconNotes as Notes,
  IconTrash as Trash2,
  IconUserPlus as UserPlus,
  IconX as X,
} from "@tabler/icons-react";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import {
  CompactSwitch,
  ConfirmModal,
  DataTableFrame,
  EmptyPanel,
  FormField,
  FormModal,
  FormSwitchField,
  FormSurface,
  IconButton,
  PawchiveIdentityFields,
  PageHeader,
  PageLoading,
} from "../components/ui";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { CreatorReference, CreatorRosterItem, CreatorSummary } from "../types";

const blankCreator: CreatorReference = {
  service: "fanbox",
  creator_id: "",
  alias: null,
  enabled: true,
};

export function CreatorsPage() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const roster = useQuery({ queryKey: ["creators"], queryFn: () => api<CreatorRosterItem[]>("/creators") });
  const [editor, setEditor] = useState<CreatorReference | null>(null);
  const [originalKey, setOriginalKey] = useState<string | null>(null);
  const [removing, setRemoving] = useState<CreatorReference | null>(null);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<CreatorSummary[]>([]);

  if (roster.isLoading) return <PageLoading />;

  function openNew(prefill?: CreatorSummary) {
    setOriginalKey(null);
    setEditor(
      prefill
        ? {
            service: prefill.service,
            creator_id: prefill.id,
            alias: prefill.name ?? null,
            enabled: true,
          }
        : { ...blankCreator },
    );
  }

  function openEdit(creator: CreatorReference) {
    setOriginalKey(`${creator.service}/${creator.creator_id}`);
    setEditor({ ...creator });
  }

  async function saveCreator(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || !session) return;
    setSaving(true);
    try {
      if (originalKey) {
        await api<CreatorReference>(`/creators/${originalKey}`, {
          method: "PUT",
          body: { alias: editor.alias || null, enabled: editor.enabled },
          csrfToken: session.csrf_token,
        });
        toast.success(t("creators.updated"));
      } else {
        await api<CreatorReference>("/creators", {
          method: "POST",
          body: editor,
          csrfToken: session.csrf_token,
        });
        toast.success(t("creators.added"));
      }
      setEditor(null);
      await queryClient.invalidateQueries({ queryKey: ["creators"] });
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSaving(false);
    }
  }

  async function setEnabled(creator: CreatorReference, enabled: boolean) {
    if (!session) return;
    try {
      await api<CreatorReference>(`/creators/${creator.service}/${creator.creator_id}`, {
        method: "PUT",
        body: { alias: creator.alias, enabled },
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["creators"] });
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  async function removeCreator() {
    if (!removing || !session) return;
    try {
      await api<CreatorReference>(`/creators/${removing.service}/${removing.creator_id}`, {
        method: "DELETE",
        csrfToken: session.csrf_token,
      });
      setRemoving(null);
      toast.success(t("creators.removed"));
      await queryClient.invalidateQueries({ queryKey: ["creators"] });
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  async function searchCreators(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!searchTerm.trim()) return;
    setSearching(true);
    try {
      const parameters = new URLSearchParams({ name: searchTerm.trim() });
      setResults(await api<CreatorSummary[]>(`/pawchive/creators?${parameters.toString()}`));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSearching(false);
    }
  }

  const creators = roster.data ?? [];
  return (
    <div className="grid gap-6">
      <PageHeader
        description={t("creators.description")}
        title={t("creators.title")}
        actions={
          <Button variant="primary" onPress={() => openNew()}>
            <Plus aria-hidden="true" size={18} />
            {t("creators.add")}
          </Button>
        }
      />

      <section className="grid gap-3">
        <h2 className="text-lg font-semibold">{t("creators.search")}</h2>
        <FormSurface className="p-3">
          <form className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2" onSubmit={searchCreators}>
            <SearchField
              aria-label={t("creators.search")}
              className="min-w-0 flex-1"
              fullWidth
              value={searchTerm}
              variant="secondary"
              onChange={setSearchTerm}
            >
              <SearchField.Group>
                <SearchField.SearchIcon>
                  <Search aria-hidden="true" size={16} />
                </SearchField.SearchIcon>
                <SearchField.Input placeholder={t("creators.searchPlaceholder")} />
                <SearchField.ClearButton aria-label={t("common.clearSearch")} />
              </SearchField.Group>
            </SearchField>
            <Button isPending={searching} type="submit" variant="primary">
              <Search aria-hidden="true" size={17} />
              {t("common.search")}
            </Button>
          </form>
        </FormSurface>
        {results.length ? (
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {results.map((creator) => (
              <Surface className="flex min-w-0 items-center gap-3 rounded-lg border border-border p-3" key={`${creator.service}:${creator.id}`}>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{creator.name || creator.id}</p>
                  <p className="truncate text-xs text-muted">{creator.service}:{creator.id}</p>
                </div>
                <IconButton icon={UserPlus} label={t("creators.add")} onPress={() => openNew(creator)} />
              </Surface>
            ))}
          </div>
        ) : null}
      </section>

      <section className="grid gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">{t("creators.roster")}</h2>
          <Chip color="accent" size="sm" variant="soft">{creators.length}</Chip>
        </div>
        {!creators.length ? (
          <EmptyPanel title={t("creators.empty")} />
        ) : (
          <>
            <DataTableFrame className="hidden lg:block">
              <Table.Content aria-label={t("creators.roster")}>
                    <Table.Header>
                      <Table.Column isRowHeader>{t("creators.creatorId")}</Table.Column>
                      <Table.Column>{t("creators.service")}</Table.Column>
                      <Table.Column>{t("creators.alias")}</Table.Column>
                      <Table.Column>{t("common.status")}</Table.Column>
                      <Table.Column className="text-right">{t("common.actions")}</Table.Column>
                    </Table.Header>
                    <Table.Body>
                      {creators.map((creator) => (
                        <Table.Row key={`${creator.service}:${creator.creator_id}`}>
                          <Table.Cell className="font-medium"><code className="text-xs">{creator.creator_id}</code></Table.Cell>
                          <Table.Cell>{creator.service}</Table.Cell>
                          <Table.Cell>{creator.alias || "—"}</Table.Cell>
                          <Table.Cell className="w-24 text-center">
                            <div className="list-switch-cell mx-auto flex w-20 items-center justify-center">
                              <CompactSwitch
                                isSelected={creator.enabled}
                                label={creator.enabled ? t("common.enabled") : t("common.disabled")}
                                onChange={(enabled) => void setEnabled(creator, enabled)}
                              />
                            </div>
                          </Table.Cell>
                          <Table.Cell className="text-right">
                            <CreatorActions creator={creator} onEdit={() => openEdit(creator)} onRemove={() => setRemoving(creator)} />
                          </Table.Cell>
                        </Table.Row>
                      ))}
                    </Table.Body>
              </Table.Content>
            </DataTableFrame>
            <div className="grid gap-3 lg:hidden">
              {creators.map((creator) => (
                <Surface className="data-mobile-card rounded-lg border border-border p-4" key={`${creator.service}:${creator.creator_id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="break-all font-medium"><code>{creator.creator_id}</code></p>
                      <p className="mt-1 text-xs text-muted">{creator.service}</p>
                    </div>
                    <CreatorActions creator={creator} onEdit={() => openEdit(creator)} onRemove={() => setRemoving(creator)} />
                  </div>
                  <div className="mt-3 grid grid-cols-[auto_minmax(0,1fr)] gap-2 text-sm">
                    <span className="text-muted">{t("creators.alias")}</span>
                    <span className="min-w-0 break-words text-right">{creator.alias || "—"}</span>
                  </div>
                  <div className="mt-4 flex min-h-14 items-center justify-between gap-3 border-t border-border pt-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium">{t("creators.enabled")}</p>
                      <p className="mt-0.5 text-xs text-muted">{creator.enabled ? t("common.enabled") : t("common.disabled")}</p>
                    </div>
                    <div className="list-switch-cell flex w-20 shrink-0 items-center justify-center">
                      <CompactSwitch
                        isSelected={creator.enabled}
                        label={creator.enabled ? t("common.enabled") : t("common.disabled")}
                        onChange={(enabled) => void setEnabled(creator, enabled)}
                      />
                    </div>
                  </div>
                </Surface>
              ))}
            </div>
          </>
        )}
      </section>

      <FormModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setEditor(null)}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
            <Button form="creator-form" isPending={saving} type="submit" variant="primary"><Check aria-hidden="true" size={17} />{t("common.save")}</Button>
          </>
        }
        open={editor !== null}
        title={originalKey ? t("creators.edit") : t("creators.add")}
        onOpenChange={(open) => !open && setEditor(null)}
      >
        {editor ? (
          <form className="grid gap-5" id="creator-form" onSubmit={saveCreator}>
            <PawchiveIdentityFields
              creatorId={editor.creator_id}
              creatorIdLabel={t("creators.creatorId")}
              description={originalKey ? t("creators.identityLockedHint") : t("creators.identityHint")}
              icon={Cloud}
              isReadOnly={Boolean(originalKey)}
              label={t("creators.identity")}
              service={editor.service}
              serviceLabel={t("creators.service")}
              onCreatorIdChange={(creator_id) => setEditor({ ...editor, creator_id })}
              onServiceChange={(service) => setEditor({ ...editor, service })}
            />
            <FormField
              description={t("creators.aliasHint")}
              icon={Notes}
              label={t("creators.alias")}
              value={editor.alias ?? ""}
              onChange={(alias) => setEditor({ ...editor, alias: alias || null })}
            />
            <FormSwitchField
              description={t("creators.enabledHint")}
              icon={Power}
              isSelected={editor.enabled}
              label={t("creators.enabled")}
              onChange={(enabled) => setEditor({ ...editor, enabled })}
            />
          </form>
        ) : null}
      </FormModal>

      <ConfirmModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setRemoving(null)}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
            <Button variant="danger" onPress={() => void removeCreator()}>
              <Trash2 aria-hidden="true" size={17} />
              {t("common.remove")}
            </Button>
          </>
        }
        open={removing !== null}
        size="md"
        title={t("creators.removeTitle")}
        onOpenChange={(open) => !open && setRemoving(null)}
      >
        <p className="text-sm leading-relaxed text-muted">{t("creators.removeBody")}</p>
      </ConfirmModal>
    </div>
  );
}

function CreatorActions({
  creator,
  onEdit,
  onRemove,
}: {
  creator: CreatorReference;
  onEdit: () => void;
  onRemove: () => void;
}) {
  const { t } = useTranslation();
  const name = `${creator.service}:${creator.creator_id}`;
  return (
    <div className="flex items-center justify-end gap-1">
      <IconButton icon={Pencil} label={`${t("common.edit")} ${name}`} onPress={onEdit} />
      <IconButton className="text-danger" icon={Trash2} label={`${t("common.remove")} ${name}`} onPress={onRemove} />
    </div>
  );
}
