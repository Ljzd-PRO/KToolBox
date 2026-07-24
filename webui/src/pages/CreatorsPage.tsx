import {
  Button,
  Chip,
  SearchField,
  Surface,
  Table,
  toast,
} from "@heroui/react";
import type { SortDescriptor } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconCheck as Check,
  IconCircleCheck as CircleCheck,
  IconCloud as Cloud,
  IconFilter as Filter,
  IconFingerprint as Fingerprint,
  IconLink as Link,
  IconPencil as Pencil,
  IconPlus as Plus,
  IconPower as Power,
  IconCircleOff as PowerOff,
  IconSearch as Search,
  IconNotes as Notes,
  IconRefresh as Sync,
  IconTool as Tools,
  IconTrash as Trash2,
  IconUser as User,
  IconUserPlus as UserPlus,
  IconUsersGroup as UsersRound,
  IconX as X,
} from "@tabler/icons-react";
import { useMemo, useState, type FormEvent } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import {
  BatchActionBar,
  CompactSwitch,
  ConfirmModal,
  DataTableFrame,
  EmptyPanel,
  FormField,
  FormModal,
  FormSwitchField,
  FormSurface,
  IconButton,
  MobileSortControls,
  PawchiveIdentityFields,
  PageHeader,
  PageLoading,
  PlatformLabel,
  SelectionCheckbox,
  SelectField,
  SortableColumn,
  TableColumnLabel,
} from "../components/ui";
import { ExternalChangeAlert } from "../components/ExternalChangeAlert";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { parsePawchiveCreatorUrl } from "../lib/pawchive";
import { useRealtime } from "../lib/realtime";
import { stableSort } from "../lib/sorting";
import type { CreatorReference, CreatorRosterItem, CreatorSummary } from "../types";

const blankCreator: CreatorReference = {
  service: "fanbox",
  creator_id: "",
  alias: null,
  enabled: true,
};

type CreatorStatusFilter = "all" | "enabled" | "disabled";
type CreatorIdentityMode = "url" | "fields";

export function CreatorsPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const realtime = useRealtime(false);
  const creatorRevision = realtime?.revisions.creators ?? 0;
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const roster = useQuery({ queryKey: ["creators"], queryFn: () => api<CreatorRosterItem[]>("/creators") });
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>({
    column: "name",
    direction: "ascending",
  });
  const [editor, setEditor] = useState<CreatorReference | null>(null);
  const [editorOriginal, setEditorOriginal] = useState<CreatorReference | null>(null);
  const [editorRevisionBaseline, setEditorRevisionBaseline] = useState(
    creatorRevision,
  );
  const [creatorIdentityMode, setCreatorIdentityMode] = useState<CreatorIdentityMode>("url");
  const [creatorUrl, setCreatorUrl] = useState("");
  const [creatorUrlError, setCreatorUrlError] = useState<string>();
  const [originalKey, setOriginalKey] = useState<string | null>(null);
  const [removing, setRemoving] = useState<CreatorReference[]>([]);
  const [deleting, setDeleting] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());
  const [batchBusy, setBatchBusy] = useState<"enable" | "disable" | null>(null);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<CreatorSummary[]>([]);
  const statusFilter = creatorStatusFilter(searchParams.get("status"));
  const creators = useMemo(() => {
    const filtered = (roster.data ?? []).filter((creator) => {
      if (statusFilter === "enabled") return creator.enabled;
      if (statusFilter === "disabled") return !creator.enabled;
      return true;
    });
    return stableSort(
      filtered,
      sortDescriptor,
      (creator, column) => {
        if (column === "name") return creator.name || creator.creator_id;
        if (column === "creator_id") return creator.creator_id;
        if (column === "service") return creator.service;
        if (column === "alias") return creator.alias;
        return creator.enabled;
      },
      i18n.resolvedLanguage ?? i18n.language,
    );
  }, [i18n.language, i18n.resolvedLanguage, roster.data, sortDescriptor, statusFilter]);
  if (roster.isLoading) return <PageLoading />;

  const selectedCreators = creators.filter((creator) => selectedKeys.has(creatorKey(creator)));
  const allVisibleSelected = creators.length > 0 && selectedCreators.length === creators.length;
  const enableCandidates = selectedCreators.filter((creator) => !creator.enabled);
  const disableCandidates = selectedCreators.filter((creator) => creator.enabled);

  function openNew(prefill?: CreatorSummary) {
    setOriginalKey(null);
    setCreatorIdentityMode(prefill ? "fields" : "url");
    setCreatorUrl("");
    setCreatorUrlError(undefined);
    const value = prefill
      ? {
          service: prefill.service,
          creator_id: prefill.id,
          alias: null,
          enabled: true,
        }
      : { ...blankCreator };
    setEditor(value);
    setEditorOriginal(value);
    setEditorRevisionBaseline(creatorRevision);
  }

  function openEdit(creator: CreatorReference) {
    setOriginalKey(`${creator.service}/${creator.creator_id}`);
    setCreatorIdentityMode("fields");
    setCreatorUrl("");
    setCreatorUrlError(undefined);
    setEditor({ ...creator });
    setEditorOriginal({ ...creator });
    setEditorRevisionBaseline(creatorRevision);
  }

  async function saveCreator(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || !session) return;
    let creator = editor;
    if (!originalKey && creatorIdentityMode === "url") {
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
      if (originalKey) {
        await api<CreatorReference>(`/creators/${originalKey}`, {
          method: "PUT",
          body: { alias: creator.alias || null, enabled: creator.enabled },
          csrfToken: session.csrf_token,
        });
        toast.success(t("creators.updated"));
      } else {
        await api<CreatorReference>("/creators", {
          method: "POST",
          body: creator,
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

  async function updateCreatorState(creator: CreatorReference, enabled: boolean) {
    if (!session) throw new Error("Session unavailable");
    await api<CreatorReference>(`/creators/${creator.service}/${creator.creator_id}`, {
      method: "PUT",
      body: { alias: creator.alias, enabled },
      csrfToken: session.csrf_token,
    });
  }

  async function setEnabled(creator: CreatorReference, enabled: boolean) {
    try {
      await updateCreatorState(creator, enabled);
      await queryClient.invalidateQueries({ queryKey: ["creators"] });
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  async function batchSetEnabled(enabled: boolean) {
    if (!session) return;
    const candidates = enabled ? enableCandidates : disableCandidates;
    if (!candidates.length) return;
    setBatchBusy(enabled ? "enable" : "disable");
    try {
      const succeeded: string[] = [];
      const errors: unknown[] = [];
      for (const creator of candidates) {
        try {
          await updateCreatorState(creator, enabled);
          succeeded.push(creatorKey(creator));
        } catch (error) {
          errors.push(error);
        }
      }
      await queryClient.invalidateQueries({ queryKey: ["creators"] });
      setSelectedKeys((current) => {
        const next = new Set(current);
        succeeded.forEach((key) => next.delete(key));
        return next;
      });
      const action = enabled ? t("creators.batchEnableAction") : t("creators.batchDisableAction");
      if (errors.length) {
        toast.danger(t("creators.batchPartial", {
          action,
          succeeded: succeeded.length,
          failed: errors.length,
        }), { description: errorText(errors[0]) });
      } else {
        toast.success(t("creators.batchCompleted", { action, count: succeeded.length }));
      }
    } finally {
      setBatchBusy(null);
    }
  }

  async function removeCreators() {
    if (!removing.length || !session) return;
    setDeleting(true);
    try {
      const batch = removing.length > 1;
      const succeeded: string[] = [];
      const failed: CreatorReference[] = [];
      const errors: unknown[] = [];
      for (const creator of removing) {
        try {
          await api<CreatorReference>(`/creators/${creator.service}/${creator.creator_id}`, {
            method: "DELETE",
            csrfToken: session.csrf_token,
          });
          succeeded.push(creatorKey(creator));
        } catch (error) {
          failed.push(creator);
          errors.push(error);
        }
      }
      setRemoving(failed);
      setSelectedKeys((current) => {
        const next = new Set(current);
        succeeded.forEach((key) => next.delete(key));
        return next;
      });
      await queryClient.invalidateQueries({ queryKey: ["creators"] });
      if (errors.length) {
        toast.danger(t("creators.batchRemovePartial", {
          succeeded: succeeded.length,
          failed: errors.length,
        }), { description: errorText(errors[0]) });
      } else if (batch) {
        toast.success(t("creators.batchRemoved", { count: succeeded.length }));
      } else {
        toast.success(t("creators.removed"));
      }
    } finally {
      setDeleting(false);
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

  const statusOptions = [
    { value: "all", label: t("creators.allStatuses"), icon: UsersRound },
    { value: "enabled", label: t("common.enabled"), icon: CircleCheck, tone: "success" as const },
    { value: "disabled", label: t("common.disabled"), icon: PowerOff },
  ];
  const sortOptions = [
    { value: "name", label: t("creators.creatorName") },
    { value: "creator_id", label: t("creators.creatorId") },
    { value: "service", label: t("creators.service") },
    { value: "alias", label: t("creators.alias") },
    { value: "status", label: t("common.status") },
  ];

  function changeStatusFilter(value: string) {
    const next = new URLSearchParams(searchParams);
    if (value === "all") next.delete("status");
    else next.set("status", value);
    setSearchParams(next, { replace: true });
  }

  function setCreatorSelected(creator: CreatorReference, selected: boolean) {
    const key = creatorKey(creator);
    setSelectedKeys((current) => {
      const next = new Set(current);
      if (selected) next.add(key);
      else next.delete(key);
      return next;
    });
  }

  function selectAllVisible(selected: boolean) {
    setSelectedKeys(selected ? new Set(creators.map(creatorKey)) : new Set());
  }

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
        <FormSurface className="grid gap-3 p-3 lg:grid-cols-[minmax(0,16rem)_minmax(0,1fr)]">
          <SelectField
            icon={Filter}
            label={t("creators.statusFilter")}
            options={statusOptions}
            value={statusFilter}
            onChange={changeStatusFilter}
          />
          <MobileSortControls
            className="lg:hidden"
            descriptor={sortDescriptor}
            options={sortOptions}
            onChange={(descriptor) => descriptor && setSortDescriptor(descriptor)}
          />
        </FormSurface>
        {selectedCreators.length ? (
          <BatchActionBar
            allVisibleSelected={allVisibleSelected}
            partiallySelected={!allVisibleSelected}
            selectedCount={selectedCreators.length}
            onClear={() => setSelectedKeys(new Set())}
            onSelectAll={selectAllVisible}
          >
            <Button
              className="semantic-action-button action-tone-enable"
              isDisabled={!enableCandidates.length || batchBusy !== null}
              isPending={batchBusy === "enable"}
              size="sm"
              variant="outline"
              onPress={() => void batchSetEnabled(true)}
            >
              <CircleCheck aria-hidden="true" size={16} />
              {t("creators.batchEnable", { count: enableCandidates.length })}
            </Button>
            <Button
              isDisabled={!disableCandidates.length || batchBusy !== null}
              isPending={batchBusy === "disable"}
              size="sm"
              variant="outline"
              onPress={() => void batchSetEnabled(false)}
            >
              <PowerOff aria-hidden="true" size={16} />
              {t("creators.batchDisable", { count: disableCandidates.length })}
            </Button>
            <Button
              isDisabled={batchBusy !== null}
              size="sm"
              variant="danger-soft"
              onPress={() => setRemoving(selectedCreators)}
            >
              <Trash2 aria-hidden="true" size={16} />
              {t("creators.batchRemove", { count: selectedCreators.length })}
            </Button>
          </BatchActionBar>
        ) : null}
        {!creators.length ? (
          <EmptyPanel title={t("creators.empty")} />
        ) : (
          <>
            <DataTableFrame className="hidden lg:block">
              <Table.Content
                aria-label={t("creators.roster")}
                sortDescriptor={sortDescriptor}
                onSortChange={setSortDescriptor}
              >
                    <Table.Header>
                      <Table.Column aria-label={t("common.select")} className="w-12">
                        <SelectionCheckbox
                          isIndeterminate={selectedCreators.length > 0 && !allVisibleSelected}
                          isSelected={allVisibleSelected}
                          label={t("common.selectAllVisible")}
                          onChange={selectAllVisible}
                        />
                      </Table.Column>
                      <SortableColumn icon={User} id="name" isRowHeader>{t("creators.creatorName")}</SortableColumn>
                      <SortableColumn icon={Fingerprint} id="creator_id">{t("creators.creatorId")}</SortableColumn>
                      <SortableColumn icon={Cloud} id="service">{t("creators.service")}</SortableColumn>
                      <SortableColumn icon={Notes} id="alias">{t("creators.alias")}</SortableColumn>
                      <SortableColumn icon={Sync} id="status">{t("creators.enabled")}</SortableColumn>
                      <Table.Column className="text-right"><TableColumnLabel className="justify-end" icon={Tools}>{t("common.actions")}</TableColumnLabel></Table.Column>
                    </Table.Header>
                    <Table.Body>
                      {creators.map((creator) => (
                        <Table.Row className={selectedKeys.has(creatorKey(creator)) ? "is-selected" : ""} key={creatorKey(creator)}>
                          <Table.Cell className="w-12">
                            <SelectionCheckbox
                              isSelected={selectedKeys.has(creatorKey(creator))}
                              label={t("creators.selectCreator", { name: creator.name || creator.creator_id })}
                              onChange={(selected) => setCreatorSelected(creator, selected)}
                            />
                          </Table.Cell>
                          <Table.Cell className="font-medium">
                            <span className="data-cell-label"><User aria-hidden="true" className="data-cell-icon" size={16} />{creator.name || creator.creator_id}</span>
                          </Table.Cell>
                          <Table.Cell className="font-medium">
                            <span className="data-cell-label"><Fingerprint aria-hidden="true" className="data-cell-icon" size={15} /><code className="text-xs">{creator.creator_id}</code></span>
                          </Table.Cell>
                          <Table.Cell><PlatformLabel platform={creator.service} /></Table.Cell>
                          <Table.Cell>
                            <span className="data-cell-label"><Notes aria-hidden="true" className="data-cell-icon" size={15} /><span>{creator.alias || "—"}</span></span>
                          </Table.Cell>
                          <Table.Cell className="w-32 text-center">
                            <div className="full-sync-cell list-switch-cell relative mx-auto flex w-28 items-center justify-center">
                              <Sync aria-hidden="true" className="data-cell-icon" size={15} />
                              <CompactSwitch
                                isSelected={creator.enabled}
                                label={creator.enabled ? t("common.enabled") : t("common.disabled")}
                                onChange={(enabled) => void setEnabled(creator, enabled)}
                              />
                            </div>
                          </Table.Cell>
                          <Table.Cell className="text-right">
                            <CreatorActions creator={creator} onEdit={() => openEdit(creator)} onRemove={() => setRemoving([creator])} />
                          </Table.Cell>
                        </Table.Row>
                      ))}
                    </Table.Body>
              </Table.Content>
            </DataTableFrame>
            <div className="grid gap-3 lg:hidden">
              {creators.map((creator) => (
                <Surface className={`data-mobile-card rounded-lg border border-border p-4${selectedKeys.has(creatorKey(creator)) ? " is-selected" : ""}`} key={creatorKey(creator)}>
                  <div className="flex items-start justify-between gap-3">
                    <SelectionCheckbox
                      className="-ml-2 shrink-0"
                      isSelected={selectedKeys.has(creatorKey(creator))}
                      label={t("creators.selectCreator", { name: creator.name || creator.creator_id })}
                      onChange={(selected) => setCreatorSelected(creator, selected)}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="data-cell-label break-words font-medium"><User aria-hidden="true" className="data-cell-icon" size={16} /><span>{creator.name || creator.creator_id}</span></p>
                      <div className="mt-1 flex min-w-0 flex-wrap items-center gap-2 text-xs text-muted">
                        <PlatformLabel platform={creator.service} />
                        <span className="data-cell-label"><Fingerprint aria-hidden="true" className="data-cell-icon" size={14} /><code className="break-all">{creator.creator_id}</code></span>
                      </div>
                    </div>
                    <CreatorActions creator={creator} onEdit={() => openEdit(creator)} onRemove={() => setRemoving([creator])} />
                  </div>
                  <div className="mt-3 grid grid-cols-[auto_minmax(0,1fr)] gap-2 text-sm">
                    <span className="data-cell-label text-muted"><Notes aria-hidden="true" className="data-cell-icon" size={15} />{t("creators.alias")}</span>
                    <span className="min-w-0 break-words text-right">{creator.alias || "—"}</span>
                  </div>
                  <div className="mt-4 flex min-h-14 items-center justify-between gap-3 border-t border-border pt-3">
                    <div className="min-w-0">
                      <p className="data-cell-label text-sm font-medium"><Sync aria-hidden="true" className="data-cell-icon" size={16} />{t("creators.enabled")}</p>
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
            <ExternalChangeAlert
              visible={Boolean(
                originalKey &&
                  editorOriginal &&
                  JSON.stringify(editor) !== JSON.stringify(editorOriginal) &&
                  creatorRevision > editorRevisionBaseline,
              )}
              onKeepEditing={() =>
                setEditorRevisionBaseline(creatorRevision)
              }
              onReload={() => setEditor(null)}
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
                value={creatorIdentityMode}
                onChange={(value) => {
                  setCreatorUrlError(undefined);
                  setCreatorIdentityMode(value === "fields" ? "fields" : "url");
                }}
              />
            ) : null}
            {!originalKey && creatorIdentityMode === "url" ? (
              <FormField
                description={t("creators.creatorUrlHint")}
                errorMessage={creatorUrlError}
                icon={Link}
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
                      components={{ code: <code className="inline-path-code" /> }}
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
            <Button variant="ghost" onPress={() => setRemoving([])}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
            <Button isPending={deleting} variant="danger" onPress={() => void removeCreators()}>
              <Trash2 aria-hidden="true" size={17} />
              {t("common.remove")}
            </Button>
          </>
        }
        open={removing.length > 0}
        size="md"
        title={removing.length > 1 ? t("creators.batchRemoveTitle", { count: removing.length }) : t("creators.removeTitle")}
        onOpenChange={(open) => !open && setRemoving([])}
      >
        <p className="text-sm leading-relaxed text-muted">
          {removing.length > 1 ? t("creators.batchRemoveBody", { count: removing.length }) : t("creators.removeBody")}
        </p>
      </ConfirmModal>
    </div>
  );
}

function creatorStatusFilter(value: string | null): CreatorStatusFilter {
  return value === "enabled" || value === "disabled" ? value : "all";
}

function creatorKey(creator: CreatorReference) {
  return `${creator.service}:${creator.creator_id}`;
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
