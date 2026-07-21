import { Button, Chip, Surface, Tabs } from "@heroui/react";
import {
  BookOpenCheck,
  CalendarRange,
  Check,
  Cloud,
  Download,
  FileJson,
  FileText,
  FilterX,
  Fingerprint,
  FolderOutput,
  History,
  Link,
  ListFilter,
  ListStart,
  Plus,
  RefreshCw,
  Shuffle,
  Tags,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { parseDate } from "@internationalized/date";

import type { CreatorReference, DownloadTaskSpec, SyncTaskSpec, TaskRecord, TaskSpec } from "../types";
import {
  AppModal,
  DateRangeInput,
  type DateRangeValue,
  FormCheckbox,
  FormField,
  FormSwitchField,
  NumberInput,
  SelectField,
} from "./ui";

export function TaskEditor({
  creators,
  task,
  saving,
  onClose,
  onSave,
}: {
  creators: CreatorReference[];
  task?: TaskRecord;
  saving: boolean;
  onClose: () => void;
  onSave: (spec: TaskSpec) => Promise<void>;
}) {
  const { t } = useTranslation();
  const initial = task?.spec;
  const [kind, setKind] = useState<"sync" | "download">(initial?.kind ?? "sync");
  const [output, setOutput] = useState(initial?.output ?? "downloads");

  const initialSync = initial?.kind === "sync" ? initial : undefined;
  const [allEnabled, setAllEnabled] = useState(!initialSync || initialSync.creators.length === 0);
  const [selectedCreators, setSelectedCreators] = useState(
    new Set((initialSync?.creators ?? []).map((creator) => `${creator.service}:${creator.creator_id}`)),
  );
  const [saveIndices, setSaveIndices] = useState(initialSync?.save_creator_indices ?? false);
  const [mixPosts, setMixPosts] = useState(initialSync?.mix_posts === null || initialSync?.mix_posts === undefined ? "inherit" : String(initialSync.mix_posts));
  const [offset, setOffset] = useState(initialSync?.offset ?? 0);
  const [length, setLength] = useState(initialSync?.length?.toString() ?? "");
  const [keywords, setKeywords] = useState((initialSync?.keywords ?? []).join(", "));
  const [excludedKeywords, setExcludedKeywords] = useState((initialSync?.keywords_exclude ?? []).join(", "));
  const initialRange = taskDateRange(initialSync);
  const [dateRange, setDateRange] = useState<DateRangeValue | null>(initialRange);
  const [useStart, setUseStart] = useState(Boolean(initialSync?.start_time));
  const [useEnd, setUseEnd] = useState(Boolean(initialSync?.end_time));

  const initialDownload = initial?.kind === "download" ? initial : undefined;
  const [downloadIdentity, setDownloadIdentity] = useState(initialDownload?.post ? "url" : "fields");
  const [postUrl, setPostUrl] = useState(initialDownload?.post ?? "");
  const [service, setService] = useState(initialDownload?.service ?? "fanbox");
  const [creatorId, setCreatorId] = useState(initialDownload?.creator_id ?? "");
  const [postId, setPostId] = useState(initialDownload?.post_id ?? "");
  const [revisionId, setRevisionId] = useState(initialDownload?.revision_id ?? "");
  const [dumpMetadata, setDumpMetadata] = useState(initialDownload?.dump_post_data ?? true);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (kind === "download") {
      const spec: DownloadTaskSpec = {
        kind,
        post: downloadIdentity === "url" ? postUrl.trim() : null,
        service: downloadIdentity === "fields" ? service.trim() : null,
        creator_id: downloadIdentity === "fields" ? creatorId.trim() : null,
        post_id: downloadIdentity === "fields" ? postId.trim() : null,
        revision_id: revisionId.trim() || null,
        output,
        dump_post_data: dumpMetadata,
      };
      await onSave(spec);
      return;
    }
    const selected = allEnabled
      ? []
      : creators.filter((creator) => selectedCreators.has(`${creator.service}:${creator.creator_id}`));
    const spec: SyncTaskSpec = {
      kind,
      creators: selected,
      output,
      save_creator_indices: saveIndices,
      mix_posts: mixPosts === "inherit" ? null : mixPosts === "true",
      start_time: useStart && dateRange ? `${dateRange.start.toString()}T00:00:00` : null,
      end_time: useEnd && dateRange ? `${dateRange.end.toString()}T23:59:59` : null,
      offset,
      length: length ? Number(length) : null,
      keywords: splitList(keywords),
      keywords_exclude: splitList(excludedKeywords),
    };
    await onSave(spec);
  }

  function toggleCreator(key: string, selected: boolean) {
    setSelectedCreators((current) => {
      const next = new Set(current);
      if (selected) next.add(key);
      else next.delete(key);
      return next;
    });
  }

  return (
    <AppModal
      footer={
        <>
          <Button variant="ghost" onPress={onClose}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
          <Button form="task-editor-form" isPending={saving} type="submit" variant="primary">
            {task ? <Check aria-hidden="true" size={17} /> : <Plus aria-hidden="true" size={17} />}
            {task ? t("common.save") : t("tasks.create")}
          </Button>
        </>
      }
      open
      formSurface
      size="lg"
      title={task ? t("tasks.edit") : t("tasks.create")}
      onOpenChange={(open) => !open && onClose()}
    >
      <form className="grid gap-6" id="task-editor-form" onSubmit={submit}>
        <Tabs selectedKey={kind} variant="secondary" onSelectionChange={(key) => setKind(String(key) as "sync" | "download")}>
          <Tabs.ListContainer>
            <Tabs.List aria-label={t("common.type")}>
              <Tabs.Tab id="sync"><RefreshCw aria-hidden="true" size={16} />{t("common.sync")}<Tabs.Indicator /></Tabs.Tab>
              <Tabs.Tab id="download"><Download aria-hidden="true" size={16} />{t("common.download")}<Tabs.Indicator /></Tabs.Tab>
            </Tabs.List>
          </Tabs.ListContainer>
          <Tabs.Panel className="grid gap-5 pt-5" id="sync">
            <section className="grid gap-3">
              <FormSwitchField
                description={t("tasks.allEnabledHint")}
                icon={UsersRound}
                isSelected={allEnabled}
                label={t("tasks.allEnabled")}
                onChange={setAllEnabled}
              />
              {!allEnabled ? (
                <Surface className="grid max-h-56 gap-1 overflow-y-auto rounded-lg border border-border p-3">
                  {creators.map((creator) => {
                    const key = `${creator.service}:${creator.creator_id}`;
                    return (
                      <FormCheckbox
                        className="w-full"
                        isSelected={selectedCreators.has(key)}
                        key={key}
                        label={
                          <span className="flex min-w-0 items-center justify-between gap-3">
                            <span className="min-w-0">
                              <span className="block truncate text-sm font-medium">{creator.alias || creator.creator_id}</span>
                              <span className="block truncate text-xs text-muted">{key}</span>
                            </span>
                            {!creator.enabled ? <Chip className="shrink-0" size="sm" variant="soft">{t("common.disabled")}</Chip> : null}
                          </span>
                        }
                        onChange={(selected) => toggleCreator(key, selected)}
                      />
                    );
                  })}
                </Surface>
              ) : null}
            </section>
            <DateRangeInput
              description={t("tasks.dateRangeHint")}
              icon={CalendarRange}
              label={t("tasks.dateRange")}
              value={dateRange}
              onChange={setDateRange}
            />
            <div className="flex flex-wrap gap-5">
              <CheckOption label={t("tasks.useStart")} selected={useStart} onChange={setUseStart} />
              <CheckOption label={t("tasks.useEnd")} selected={useEnd} onChange={setUseEnd} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <NumberInput icon={ListStart} label={t("tasks.offset")} minValue={0} step={50} value={offset} onChange={setOffset} />
              <FormField icon={ListFilter} label={t("tasks.limit")} type="number" value={length} onChange={setLength} />
              <SelectField
                icon={Shuffle}
                label={t("tasks.mixPosts")}
                options={[
                  { value: "inherit", label: t("tasks.useConfiguration") },
                  { value: "true", label: t("common.enabled") },
                  { value: "false", label: t("common.disabled") },
                ]}
                value={mixPosts}
                onChange={setMixPosts}
              />
            </div>
            <FormField description={t("tasks.keywordHint")} icon={Tags} label={t("tasks.keywords")} value={keywords} onChange={setKeywords} />
            <FormField description={t("tasks.keywordHint")} icon={FilterX} label={t("tasks.excludedKeywords")} value={excludedKeywords} onChange={setExcludedKeywords} />
            <FormSwitchField icon={BookOpenCheck} isSelected={saveIndices} label={t("tasks.saveIndex")} onChange={setSaveIndices} />
          </Tabs.Panel>
          <Tabs.Panel className="grid gap-5 pt-5" id="download">
            <SelectField
              icon={Fingerprint}
              label={t("tasks.identityMode")}
              options={[
                { value: "url", label: t("tasks.postUrl") },
                { value: "fields", label: t("tasks.identityFields") },
              ]}
              value={downloadIdentity}
              onChange={setDownloadIdentity}
            />
            {downloadIdentity === "url" ? (
              <FormField icon={Link} isRequired label={t("tasks.postUrl")} value={postUrl} onChange={setPostUrl} />
            ) : (
              <div className="grid gap-4 sm:grid-cols-3">
                <FormField icon={Cloud} isRequired label={t("posts.service")} value={service} onChange={setService} />
                <FormField icon={UserRound} isRequired label={t("posts.creatorId")} value={creatorId} onChange={setCreatorId} />
                <FormField icon={FileText} isRequired label={t("posts.postId")} value={postId} onChange={setPostId} />
              </div>
            )}
            <FormField icon={History} label={t("tasks.revision")} value={revisionId} onChange={setRevisionId} />
            <FormSwitchField icon={FileJson} isSelected={dumpMetadata} label={t("tasks.dumpMetadata")} onChange={setDumpMetadata} />
          </Tabs.Panel>
        </Tabs>
        <FormField icon={FolderOutput} isRequired label={t("tasks.output")} value={output} onChange={setOutput} />
      </form>
    </AppModal>
  );
}

function CheckOption({
  label,
  selected,
  onChange,
}: {
  label: string;
  selected: boolean;
  onChange: (selected: boolean) => void;
}) {
  return <FormCheckbox isSelected={selected} label={label} onChange={onChange} />;
}

function splitList(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function taskDateRange(spec: SyncTaskSpec | undefined): DateRangeValue | null {
  if (!spec?.start_time && !spec?.end_time) return null;
  const start = parseDate((spec.start_time ?? spec.end_time ?? "").slice(0, 10));
  const end = parseDate((spec.end_time ?? spec.start_time ?? "").slice(0, 10));
  return { start, end };
}
