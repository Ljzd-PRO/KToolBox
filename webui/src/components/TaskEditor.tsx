import { Button, Chip, Surface, Tabs } from "@heroui/react";
import {
  IconArrowsShuffle as Shuffle,
  IconAdjustments as Adjustments,
  IconBook2 as BookOpenCheck,
  IconCalendar as CalendarRange,
  IconCheck as Check,
  IconCloud as Cloud,
  IconDownload as Download,
  IconFilter as Filter,
  IconFilterX as FilterX,
  IconFingerprint as Fingerprint,
  IconFolder as FolderOutput,
  IconHistory as History,
  IconJson as FileJson,
  IconLink as Link,
  IconList as ListStart,
  IconListSearch as ListFilter,
  IconPlus as Plus,
  IconPhoto as Photo,
  IconRefresh as RefreshCw,
  IconTags as Tags,
  IconToggleLeft as ToggleLeft,
  IconToggleRight as ToggleRight,
  IconUserPlus as UserPlus,
  IconUsersGroup as UsersRound,
  IconX as X,
} from "@tabler/icons-react";
import { useState, type FormEvent } from "react";
import { Trans, useTranslation } from "react-i18next";
import { parseDate, type DateValue } from "@internationalized/date";

import type { CreatorReference, CreatorRosterItem, DownloadTaskSpec, SyncTaskSpec, TaskRecord, TaskSpec } from "../types";
import { TASK_OUTPUT_PATH_SELECTOR } from "../lib/pathSelectors";
import { useRealtime } from "../lib/realtime";
import { ExternalChangeAlert } from "./ExternalChangeAlert";
import { CreatorEditorModal, type CreatorEditorRequest } from "./CreatorEditorModal";
import { CreatorAvatar } from "./SensitiveMedia";
import { RemotePathField } from "./RemotePathField";
import {
  AddressText,
  ChipListField,
  FormCheckbox,
  FormField,
  FormModal,
  FormSwitchField,
  InlineCode,
  NumberInput,
  OptionalDateRangeField,
  PawchiveIdentityFields,
  SelectField,
} from "./ui";

export function TaskEditor({
  creators,
  defaultOutput,
  task,
  saving,
  onClose,
  onSave,
}: {
  creators: CreatorRosterItem[];
  defaultOutput: string;
  task?: TaskRecord;
  saving: boolean;
  onClose: () => void;
  onSave: (spec: TaskSpec) => Promise<void>;
}) {
  const { t } = useTranslation();
  const realtime = useRealtime(false);
  const initial = task?.spec;
  const [taskRevisionBaseline, setTaskRevisionBaseline] = useState(
    task ? (realtime?.taskDefinitionRevisions[task.id] ?? 0) : 0,
  );
  const [connectionRevisionBaseline, setConnectionRevisionBaseline] = useState(
    realtime?.revisions.tasks ?? 0,
  );
  const [kind, setKind] = useState<"sync" | "download">(initial?.kind ?? "sync");
  const [output, setOutput] = useState(initial?.output ?? defaultOutput);

  const initialSync = initial?.kind === "sync" ? initial : undefined;
  const [allEnabled, setAllEnabled] = useState(!initialSync || initialSync.creators.length === 0);
  const [additionalCreators, setAdditionalCreators] = useState<CreatorReference[]>(() =>
    (initialSync?.creators ?? []).filter(
      (candidate) =>
        !creators.some(
          (creator) =>
            creator.service === candidate.service &&
            creator.creator_id === candidate.creator_id,
        ),
    ),
  );
  const [selectedCreators, setSelectedCreators] = useState(
    new Set((initialSync?.creators ?? []).map((creator) => `${creator.service}:${creator.creator_id}`)),
  );
  const [creatorEditorRequest, setCreatorEditorRequest] = useState<CreatorEditorRequest | null>(null);
  const [saveIndices, setSaveIndices] = useState(initialSync?.save_creator_indices ?? false);
  const [mixPosts, setMixPosts] = useState(initialSync?.mix_posts === null || initialSync?.mix_posts === undefined ? "inherit" : String(initialSync.mix_posts));
  const [syncDownloadFile, setSyncDownloadFile] = useState(initialSync?.download_file ?? true);
  const [offset, setOffset] = useState(initialSync?.offset ?? 0);
  const [length, setLength] = useState(initialSync?.length?.toString() ?? "");
  const [keywords, setKeywords] = useState(initialSync?.keywords ?? []);
  const [excludedKeywords, setExcludedKeywords] = useState(initialSync?.keywords_exclude ?? []);
  const [startDate, setStartDate] = useState<DateValue | null>(taskDate(initialSync?.start_time));
  const [endDate, setEndDate] = useState<DateValue | null>(taskDate(initialSync?.end_time));
  const [startUnlimited, setStartUnlimited] = useState(!initialSync?.start_time);
  const [endUnlimited, setEndUnlimited] = useState(!initialSync?.end_time);
  const [dateError, setDateError] = useState<string | undefined>();

  const initialDownload = initial?.kind === "download" ? initial : undefined;
  const [downloadIdentity, setDownloadIdentity] = useState<"url" | "fields">(
    initialDownload ? (initialDownload.post ? "url" : "fields") : "url",
  );
  const [postUrl, setPostUrl] = useState(initialDownload?.post ?? "");
  const [service, setService] = useState(initialDownload?.service ?? "fanbox");
  const [creatorId, setCreatorId] = useState(initialDownload?.creator_id ?? "");
  const [postId, setPostId] = useState(initialDownload?.post_id ?? "");
  const [revisionId, setRevisionId] = useState(initialDownload?.revision_id ?? "");
  const [dumpMetadata, setDumpMetadata] = useState(initialDownload?.dump_post_data ?? true);
  const [postDownloadFile, setPostDownloadFile] = useState(initialDownload?.download_file ?? true);
  const availableCreators = [
    ...creators,
    ...additionalCreators.filter(
      (candidate) =>
        !creators.some(
          (creator) =>
            creator.service === candidate.service &&
            creator.creator_id === candidate.creator_id,
        ),
    ),
  ];

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (kind === "sync") {
      const nextDateError = validateDates();
      setDateError(nextDateError);
      if (nextDateError) return;
    }
    await onSave(buildSpec());
  }

  function buildSpec(): TaskSpec {
    if (kind === "download") {
      return {
        kind,
        post: downloadIdentity === "url" ? postUrl.trim() : null,
        service: downloadIdentity === "fields" ? service.trim() : null,
        creator_id: downloadIdentity === "fields" ? creatorId.trim() : null,
        post_id: downloadIdentity === "fields" ? postId.trim() : null,
        revision_id: revisionId.trim() || null,
        output,
        dump_post_data: dumpMetadata,
        download_file: postDownloadFile,
      } satisfies DownloadTaskSpec;
    }
    const selected = allEnabled
      ? []
      : availableCreators
          .filter((creator) =>
            selectedCreators.has(`${creator.service}:${creator.creator_id}`),
          )
          .map(({ service, creator_id, alias, enabled }) => ({
            service,
            creator_id,
            alias,
            enabled,
          }));
    return {
      kind,
      creators: selected,
      output,
      save_creator_indices: saveIndices,
      mix_posts: mixPosts === "inherit" ? null : mixPosts === "true",
      download_file: syncDownloadFile,
      start_time: startUnlimited || !startDate ? null : `${startDate.toString()}T00:00:00`,
      end_time: endUnlimited || !endDate ? null : `${endDate.toString()}T23:59:59`,
      offset,
      length: length ? Number(length) : null,
      keywords,
      keywords_exclude: excludedKeywords,
    } satisfies SyncTaskSpec;
  }

  function validateDates(): string | undefined {
    if (!startUnlimited && !startDate) return t("tasks.startDateRequired");
    if (!endUnlimited && !endDate) return t("tasks.endDateRequired");
    if (startDate && endDate && startDate.compare(endDate) > 0) return t("tasks.dateRangeInvalid");
    return undefined;
  }

  function toggleCreator(key: string, selected: boolean) {
    setSelectedCreators((current) => {
      const next = new Set(current);
      if (selected) next.add(key);
      else next.delete(key);
      return next;
    });
  }

  function addCreator(creator: CreatorReference) {
    const key = `${creator.service}:${creator.creator_id}`;
    if (!availableCreators.some((candidate) => `${candidate.service}:${candidate.creator_id}` === key)) {
      setAdditionalCreators((current) => [...current, creator]);
    }
    setSelectedCreators((current) => new Set(current).add(key));
  }

  const taskRevision = task ? (realtime?.taskDefinitionRevisions[task.id] ?? 0) : 0;
  const connectionRevision = realtime?.revisions.tasks ?? 0;
  const dirty = Boolean(task && JSON.stringify(buildSpec()) !== JSON.stringify(task.spec));
  const externallyChanged = Boolean(
    task &&
      dirty &&
      (taskRevision > taskRevisionBaseline ||
        connectionRevision > connectionRevisionBaseline),
  );

  return (
    <>
      <FormModal
        actions={
          <>
            <Button variant="ghost" onPress={onClose}>
              <X aria-hidden="true" size={17} />
              {t("common.cancel")}
            </Button>
            <Button form="task-editor-form" isPending={saving} type="submit" variant="primary">
              {task ? <Check aria-hidden="true" size={17} /> : <Plus aria-hidden="true" size={17} />}
              {task ? t("common.save") : t("tasks.create")}
            </Button>
          </>
        }
        isWide
        open
        size="lg"
        title={task ? t("tasks.edit") : t("tasks.create")}
        onOpenChange={(open) => !open && onClose()}
      >
        <form className="grid gap-6" id="task-editor-form" onSubmit={submit}>
        <ExternalChangeAlert
          visible={externallyChanged}
          onKeepEditing={() => {
            setTaskRevisionBaseline(taskRevision);
            setConnectionRevisionBaseline(connectionRevision);
          }}
          onReload={onClose}
        />
        <Tabs className="task-editor-tabs" selectedKey={kind} variant="secondary" onSelectionChange={(key) => setKind(String(key) as "sync" | "download")}>
          <Tabs.List aria-label={t("common.type")}>
            <Tabs.Tab id="sync"><RefreshCw aria-hidden="true" size={16} />{t("tasks.syncAuthor")}<Tabs.Indicator /></Tabs.Tab>
            <Tabs.Tab id="download"><Download aria-hidden="true" size={16} />{t("tasks.downloadPost")}<Tabs.Indicator /></Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel className="grid gap-5 pt-5" id="sync">
            <PanelIntroduction icon={RefreshCw} text={t("tasks.syncIntro")} />
            <section className="grid gap-3">
              <FormSwitchField
                description={t("tasks.allEnabledHint")}
                icon={UsersRound}
                isSelected={allEnabled}
                label={t("tasks.allEnabled")}
                onChange={setAllEnabled}
              />
              {!allEnabled ? (
                <Surface className="overflow-hidden rounded-lg border border-border">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-[var(--surface-secondary)] px-3 py-2.5">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-foreground">{t("tasks.syncTargets")}</p>
                      <p className="mt-0.5 text-xs leading-relaxed text-muted">
                        {t("tasks.creatorSelectionHint", { count: selectedCreators.size })}
                      </p>
                    </div>
                    <Button size="sm" variant="outline" onPress={() => setCreatorEditorRequest({ kind: "create" })}>
                      <UserPlus aria-hidden="true" size={16} />
                      {t("creators.add")}
                    </Button>
                  </div>
                  <div className="grid max-h-56 gap-1 overflow-y-auto p-2">
                    {availableCreators.length ? availableCreators.map((creator) => {
                      const key = `${creator.service}:${creator.creator_id}`;
                      return (
                        <FormCheckbox
                          className="w-full"
                          isSelected={selectedCreators.has(key)}
                          key={key}
                          label={
                            <span className="flex min-w-0 items-center gap-3">
                              <CreatorAvatar
                                asset={creatorAvatar(creator)}
                                name={creatorDisplayName(creator)}
                                size="xs"
                              />
                              <span className="min-w-0 flex-1">
                                <span className="block truncate text-sm font-medium">
                                  {creatorDisplayName(creator)}
                                </span>
                                <span className="block truncate text-xs text-muted">{key}</span>
                              </span>
                              {!creator.enabled ? (
                                <Chip className="shrink-0" size="sm" variant="soft">
                                  {t("common.disabled")}
                                </Chip>
                              ) : null}
                            </span>
                          }
                          onChange={(selected) => toggleCreator(key, selected)}
                        />
                      );
                    }) : (
                      <p className="px-2 py-5 text-center text-sm text-muted">{t("creators.empty")}</p>
                    )}
                  </div>
                </Surface>
              ) : null}
            </section>
            <OptionalDateRangeField
              description={t("tasks.dateRangeHint")}
              endLabel={t("tasks.endDate")}
              endUnlimited={endUnlimited}
              endUnlimitedLabel={t("tasks.noEndDate")}
              endValue={endDate}
              errorMessage={dateError}
              icon={CalendarRange}
              label={t("tasks.dateRange")}
              startLabel={t("tasks.startDate")}
              startUnlimited={startUnlimited}
              startUnlimitedLabel={t("tasks.noStartDate")}
              startValue={startDate}
              onEndChange={(value) => {
                setDateError(undefined);
                setEndDate(value);
              }}
              onEndUnlimitedChange={(selected) => {
                setDateError(undefined);
                setEndUnlimited(selected);
              }}
              onStartChange={(value) => {
                setDateError(undefined);
                setStartDate(value);
              }}
              onStartUnlimitedChange={(selected) => {
                setDateError(undefined);
                setStartUnlimited(selected);
              }}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <NumberInput description={t("tasks.offsetHint")} icon={ListStart} label={t("tasks.offset")} minValue={0} step={50} value={offset} onChange={setOffset} />
              <FormField description={t("tasks.limitHint")} icon={ListFilter} label={t("tasks.limit")} type="number" value={length} onChange={setLength} />
              <SelectField
                description={t("tasks.mixPostsHint")}
                icon={Shuffle}
                label={t("tasks.mixPosts")}
                options={[
                  { value: "inherit", label: t("tasks.useConfiguration"), icon: Adjustments },
                  { value: "true", label: t("common.enabled"), icon: ToggleRight, tone: "success" },
                  { value: "false", label: t("common.disabled"), icon: ToggleLeft },
                ]}
                value={mixPosts}
                onChange={setMixPosts}
              />
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <FormSwitchField description={t("tasks.downloadPrimaryFileHint")} icon={Photo} isSelected={syncDownloadFile} label={t("tasks.downloadPrimaryFile")} onChange={setSyncDownloadFile} />
              <FormSwitchField description={t("tasks.saveIndexHint")} icon={BookOpenCheck} isSelected={saveIndices} label={t("tasks.saveIndex")} onChange={setSaveIndices} />
            </div>
            <section className="grid gap-4 border-t border-border pt-5">
              <div className="flex items-start gap-2">
                <Filter aria-hidden="true" className="mt-0.5 shrink-0 text-accent" size={18} />
                <div className="min-w-0">
                  <h3 className="font-semibold text-foreground">{t("tasks.filterTitle")}</h3>
                  <p className="mt-1 text-xs leading-relaxed text-muted">{t("tasks.filterDescription")}</p>
                </div>
              </div>
              <ChipListField
                description={t("tasks.keywordsHint")}
                icon={Tags}
                label={t("tasks.keywords")}
                placeholder={t("tasks.keywordPlaceholder")}
                values={keywords}
                onChange={setKeywords}
              />
              <ChipListField
                description={t("tasks.excludedKeywordsHint")}
                icon={FilterX}
                label={t("tasks.excludedKeywords")}
                placeholder={t("tasks.keywordPlaceholder")}
                values={excludedKeywords}
                onChange={setExcludedKeywords}
              />
            </section>
          </Tabs.Panel>
          <Tabs.Panel className="grid gap-5 pt-5" id="download">
            <PanelIntroduction icon={Download} text={t("tasks.downloadIntro")} />
            <SelectField
              description={t("tasks.identityModeHint")}
              icon={Fingerprint}
              label={t("tasks.identityMode")}
              options={[
                { value: "url", label: t("tasks.identityUrl"), icon: Link },
                { value: "fields", label: t("tasks.identityFields"), icon: Fingerprint },
              ]}
              value={downloadIdentity}
              onChange={(value) => setDownloadIdentity(value === "fields" ? "fields" : "url")}
            />
            {downloadIdentity === "url" ? (
              <FormField
                description={<AddressText text={t("tasks.postUrlHint")} />}
                icon={Link}
                inputClassName="font-mono text-[0.8125rem]"
                isRequired
                label={t("tasks.postUrl")}
                value={postUrl}
                onChange={setPostUrl}
              />
            ) : (
              <PawchiveIdentityFields
                creatorId={creatorId}
                creatorIdLabel={t("posts.creatorId")}
                description={
                  <Trans
                    components={{ code: <InlineCode /> }}
                    i18nKey="tasks.identityPathHint"
                  />
                }
                icon={Cloud}
                label={t("tasks.identityPath")}
                postId={postId}
                postIdLabel={t("posts.postId")}
                service={service}
                serviceLabel={t("posts.service")}
                onCreatorIdChange={setCreatorId}
                onPostIdChange={setPostId}
                onServiceChange={setService}
              />
            )}
            <FormField
              description={
                <Trans
                  components={{
                    example: <span className="mt-1 block" />,
                    code: <InlineCode className="break-words" />,
                    id: <InlineCode />,
                  }}
                  i18nKey="tasks.revisionHint"
                />
              }
              icon={History}
              label={t("tasks.revision")}
              value={revisionId}
              onChange={setRevisionId}
            />
            <div className="grid gap-3 md:grid-cols-2">
              <FormSwitchField description={t("tasks.downloadPrimaryFileHint")} icon={Photo} isSelected={postDownloadFile} label={t("tasks.downloadPrimaryFile")} onChange={setPostDownloadFile} />
              <FormSwitchField description={t("tasks.dumpMetadataHint")} icon={FileJson} isSelected={dumpMetadata} label={t("tasks.dumpMetadata")} onChange={setDumpMetadata} />
            </div>
          </Tabs.Panel>
        </Tabs>
        <RemotePathField
          description={t("tasks.outputHint")}
          icon={FolderOutput}
          isRequired
          label={t("tasks.output")}
          selector={TASK_OUTPUT_PATH_SELECTOR}
          value={output}
          onChange={setOutput}
        />
        </form>
      </FormModal>
      {creatorEditorRequest ? (
        <CreatorEditorModal
          request={creatorEditorRequest}
          onClose={() => setCreatorEditorRequest(null)}
          onSaved={addCreator}
        />
      ) : null}
    </>
  );
}

function PanelIntroduction({ icon: Icon, text }: { icon: typeof RefreshCw; text: string }) {
  return (
    <div className="flex items-start gap-2 border-b border-border pb-4 text-sm leading-relaxed text-muted">
      <Icon aria-hidden="true" className="mt-0.5 shrink-0 text-accent" size={18} />
      <p>{text}</p>
    </div>
  );
}

function taskDate(value: string | null | undefined): DateValue | null {
  return value ? parseDate(value.slice(0, 10)) : null;
}

function creatorDisplayName(creator: CreatorReference | CreatorRosterItem): string {
  return "name" in creator && typeof creator.name === "string" && creator.name
    ? creator.name
    : creator.alias || creator.creator_id;
}

function creatorAvatar(creator: CreatorReference | CreatorRosterItem): CreatorRosterItem["avatar"] {
  return (creator as CreatorRosterItem).avatar;
}
