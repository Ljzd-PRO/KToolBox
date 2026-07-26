import {
  Alert,
  Button,
  Chip,
  ProgressBar,
  Surface,
  Table,
  Tabs,
  Tooltip,
  toast,
} from "@heroui/react";
import type { SortDescriptor } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconAlertTriangle as AlertTriangle,
  IconArchive as Archive,
  IconBraces as Braces,
  IconCalendarMonth as CalendarMonth,
  IconCalendarStats as CalendarStats,
  IconCheck as Check,
  IconChevronRight as ChevronRight,
  IconFile as File,
  IconFileCode as FileCode,
  IconFileDescription as FileDescription,
  IconFiles as Files,
  IconFolder as Folder,
  IconFolderCog as FolderCog,
  IconFolderOpen as FolderOpen,
  IconFolderPlus as FolderPlus,
  IconHistory as History,
  IconInfoCircle as InfoCircle,
  IconListNumbers as ListNumbers,
  IconPlayerStop as PlayerStop,
  IconRefresh as Refresh,
  IconRestore as Restore,
  IconScan as Scan,
  IconSettings as Settings,
  IconTags as Tags,
  IconTrash as Trash,
  IconUser as User,
  IconUsers as Users,
  IconX as X,
} from "@tabler/icons-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ExternalChangeAlert } from "../components/ExternalChangeAlert";
import { RemotePathField } from "../components/RemotePathField";
import {
  BatchActionBar,
  ChipListField,
  DataTableFrame,
  EmptyPanel,
  FormField,
  FormModal,
  FormSurface,
  FormSwitchField,
  InlineCode,
  PageHeader,
  PageLoading,
  SelectionCheckbox,
  SortableColumn,
  TableColumnLabel,
} from "../components/ui";
import { api, ApiError, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatBytes, formatDateTime } from "../lib/format";
import { useRealtime } from "../lib/realtime";
import type {
  NamingConfigurationResponse,
  NamingConversion,
  NamingCreatorPreview,
  NamingPreview,
  ProjectNamingConfiguration,
} from "../types";

type NamingDraft = Required<
  Omit<
    ProjectNamingConfiguration,
    "download_roots" | "post_structure" | "sequential_filename_excludes"
  >
> & {
  download_roots: string[];
  post_structure: {
    attachments: string;
    content: string;
    external_links: string;
    file: string;
    revisions: string;
  };
  sequential_filename_excludes: string[];
};

const creatorVariables = ["creator_name", "creator_id", "service"] as const;
const workVariables = [
  "id",
  "post_id",
  "user",
  "creator_id",
  "service",
  "title",
  "added",
  "published",
  "edited",
] as const;
const revisionVariables = [...workVariables, "revision_id"] as const;
const dateVariables = ["year", "month"] as const;
const activeConversionStatuses = new Set(["queued", "running", "rolling_back"]);

function normalizeNaming(value: ProjectNamingConfiguration): NamingDraft {
  return {
    download_roots: [...(value.download_roots ?? [])],
    creator_dirname_format: value.creator_dirname_format,
    post_dirname_format: value.post_dirname_format,
    revision_dirname_format: value.revision_dirname_format,
    post_structure: {
      attachments: value.post_structure?.attachments ?? "attachments",
      content: value.post_structure?.content ?? "content.txt",
      external_links: value.post_structure?.external_links ?? "external_links.txt",
      file: value.post_structure?.file ?? "{id}_{}",
      revisions: value.post_structure?.revisions ?? "revisions",
    },
    mix_posts: value.mix_posts,
    sequential_filename: value.sequential_filename,
    sequential_filename_excludes: [...(value.sequential_filename_excludes ?? [])],
    filename_format: value.filename_format,
    group_by_year: value.group_by_year,
    group_by_month: value.group_by_month,
    year_dirname_format: value.year_dirname_format,
    month_dirname_format: value.month_dirname_format,
  };
}

function draftKey(value: NamingDraft | ProjectNamingConfiguration): string {
  return JSON.stringify(normalizeNaming(value));
}

function formatTemplate(
  template: string,
  values: Record<string, string | number>,
  automatic = "",
): string {
  return template
    .replace("{}", automatic)
    .replace(/\{([a-z_]+)(?::[^}]+)?\}/giu, (token, name: string) =>
      name in values ? String(values[name]) : token,
    );
}

function sampleTree(naming: NamingDraft): Array<{ depth: number; kind: "folder" | "file"; name: string }> {
  const values = {
    creator_name: "Sample Creator",
    creator_id: "123456",
    user: "123456",
    service: "fanbox",
    id: "987654",
    post_id: "987654",
    revision_id: "3",
    title: "Sample Work",
    added: "2026-07-26",
    published: "2026-07-20",
    edited: "2026-07-24",
    year: 2026,
    month: 7,
  };
  const creator = formatTemplate(naming.creator_dirname_format, values);
  const work = formatTemplate(naming.post_dirname_format, values);
  const revision = formatTemplate(naming.revision_dirname_format, values);
  const year = formatTemplate(naming.year_dirname_format, values);
  const month = formatTemplate(naming.month_dirname_format, values);
  const primary = formatTemplate(naming.post_structure.file, values, "cover.jpg");
  const attachment = formatTemplate(naming.filename_format, values, "illustration.png");
  const tree: Array<{ depth: number; kind: "folder" | "file"; name: string }> = [
    { depth: 0, kind: "folder", name: creator },
  ];
  let depth = 1;
  if (naming.group_by_year) {
    tree.push({ depth, kind: "folder", name: year });
    depth += 1;
  }
  if (naming.group_by_month) {
    tree.push({ depth, kind: "folder", name: month });
    depth += 1;
  }
  if (!naming.mix_posts) {
    tree.push({ depth, kind: "folder", name: work });
    depth += 1;
  }
  tree.push(
    { depth, kind: "file", name: primary },
    { depth, kind: "file", name: naming.post_structure.content },
    { depth, kind: "file", name: naming.post_structure.external_links },
    { depth, kind: "folder", name: naming.post_structure.attachments },
    { depth: depth + 1, kind: "file", name: attachment },
    { depth, kind: "folder", name: naming.post_structure.revisions },
    { depth: depth + 1, kind: "folder", name: revision },
  );
  return tree;
}

function invalidTemplate(
  value: string,
  variables: readonly string[],
): "empty" | "separator" | "braces" | string | null {
  if (!value.trim()) return "empty";
  if (/[\\/]/u.test(value)) return "separator";
  if ((value.match(/\{/gu)?.length ?? 0) !== (value.match(/\}/gu)?.length ?? 0)) return "braces";
  for (const match of value.matchAll(/\{([a-z_]+)(?::[^}]+)?\}/giu)) {
    if (!variables.includes(match[1])) return match[1];
  }
  return null;
}

function invalidRelativePath(value: string): boolean {
  return !value.trim() || value.startsWith("/") || value.split(/[\\/]/u).includes("..");
}

export function NamingPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const realtime = useRealtime(false);
  const queryClient = useQueryClient();
  const namingQuery = useQuery({
    queryKey: ["naming"],
    queryFn: () => api<NamingConfigurationResponse>("/naming"),
  });
  const conversionsQuery = useQuery({
    queryKey: ["naming-conversions"],
    queryFn: () => api<NamingConversion[]>("/naming/conversions"),
  });
  const [draft, setDraft] = useState<NamingDraft | null>(null);
  const [baselineRevision, setBaselineRevision] = useState("");
  const [preview, setPreview] = useState<NamingPreview | null>(null);
  const [selectedCreators, setSelectedCreators] = useState<Set<string>>(new Set());
  const [convertExisting, setConvertExisting] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [applying, setApplying] = useState(false);
  const [historySort, setHistorySort] = useState<SortDescriptor>({
    column: "created_at",
    direction: "descending",
  });
  const [cancelTarget, setCancelTarget] = useState<NamingConversion | null>(null);

  const remoteNamingRevision = realtime?.revisions.naming ?? 0;
  const current = namingQuery.data;
  const dirty =
    draft !== null &&
    current !== undefined &&
    draftKey(draft) !== draftKey(current.naming);
  const externalChange =
    dirty && Boolean(baselineRevision) && current?.revision !== baselineRevision;
  const activeConversion = conversionsQuery.data?.find((item) =>
    activeConversionStatuses.has(item.status),
  );

  useEffect(() => {
    if (!current) return;
    if (!draft || !dirty || draftKey(draft) === draftKey(current.naming)) {
      const timer = window.setTimeout(() => {
        setDraft(normalizeNaming(current.naming));
        setBaselineRevision(current.revision);
      }, 0);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [current, dirty, draft, remoteNamingRevision]);

  const templateProblems = useMemo(() => {
    if (!draft) return [];
    return [
      ["creator_dirname_format", invalidTemplate(draft.creator_dirname_format, creatorVariables)],
      ["post_dirname_format", invalidTemplate(draft.post_dirname_format, workVariables)],
      ["revision_dirname_format", invalidTemplate(draft.revision_dirname_format, revisionVariables)],
      ["post_structure.file", invalidTemplate(draft.post_structure.file, workVariables)],
      ["filename_format", invalidTemplate(draft.filename_format, workVariables)],
      ["year_dirname_format", invalidTemplate(draft.year_dirname_format, dateVariables)],
      ["month_dirname_format", invalidTemplate(draft.month_dirname_format, dateVariables)],
    ].filter((entry): entry is [string, string] => entry[1] !== null);
  }, [draft]);
  const pathProblems = useMemo(() => {
    if (!draft) return [];
    return Object.entries(draft.post_structure)
      .filter(([name, value]) => name !== "file" && invalidRelativePath(value))
      .map(([name]) => name);
  }, [draft]);
  const rootProblems = useMemo(() => {
    if (!draft) return [];
    const normalized = draft.download_roots.map((root) => root.trim());
    return normalized.map((root, index) =>
      !root
        ? "empty"
        : normalized.indexOf(root) !== index
          ? "duplicate"
          : null,
    );
  }, [draft]);
  const hasValidationErrors =
    templateProblems.length > 0 ||
    pathProblems.length > 0 ||
    rootProblems.some(Boolean) ||
    Boolean(draft?.group_by_month && !draft.group_by_year);
  const tree = useMemo(() => (draft ? sampleTree(draft) : []), [draft]);
  const sortedConversions = useMemo(() => {
    const values = [...(conversionsQuery.data ?? [])];
    const column = String(historySort.column ?? "created_at");
    const direction = historySort.direction === "ascending" ? 1 : -1;
    return values.sort((left, right) => {
      const leftValue = column === "status" ? left.status : left.created_at;
      const rightValue = column === "status" ? right.status : right.created_at;
      return leftValue.localeCompare(rightValue, i18n.language, { numeric: true }) * direction;
    });
  }, [conversionsQuery.data, historySort, i18n.language]);

  if (namingQuery.isLoading || conversionsQuery.isLoading || !draft || !current) {
    return <PageLoading />;
  }

  function updateDraft(update: (value: NamingDraft) => NamingDraft) {
    setDraft((value) => (value ? update(value) : value));
  }

  function updateStructure(
    key: keyof NamingDraft["post_structure"],
    value: string,
  ) {
    updateDraft((currentDraft) => ({
      ...currentDraft,
      post_structure: { ...currentDraft.post_structure, [key]: value },
    }));
  }

  function addDownloadRoot() {
    if (!current || !draft) return;
    const suggested = current.suggested_download_roots?.find(
      (root) => !draft.download_roots.includes(root),
    );
    updateDraft((value) => ({
      ...value,
      download_roots: [...value.download_roots, suggested ?? ""],
    }));
  }

  async function scanPreview() {
    if (!session || hasValidationErrors) return;
    setScanning(true);
    try {
      const result = await api<NamingPreview>("/naming/preview", {
        method: "POST",
        body: { naming: draft },
        csrfToken: session.csrf_token,
      });
      setPreview(result);
      setSelectedCreators(
        new Set(result.creators.filter((creator) => creator.selectable).map((creator) => creator.key)),
      );
      setConvertExisting(true);
    } catch (error) {
      toast.danger(t("naming.previewFailed"), {
        description: namingErrorText(error, t),
      });
    } finally {
      setScanning(false);
    }
  }

  async function applyPreview() {
    if (!session || !preview) return;
    setApplying(true);
    try {
      const result = await api<NamingConversion>("/naming/apply", {
        method: "POST",
        body: {
          preview_id: preview.id,
          selected_creators: [...selectedCreators],
          convert_existing: convertExisting,
        },
        csrfToken: session.csrf_token,
      });
      setPreview(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["naming"] }),
        queryClient.invalidateQueries({ queryKey: ["naming-conversions"] }),
      ]);
      toast.success(
        t(convertExisting ? "naming.conversionStarted" : "naming.saved"),
        result.status === "completed"
          ? undefined
          : { description: t("naming.conversionBackground") },
      );
    } catch (error) {
      toast.danger(t("common.error"), { description: namingErrorText(error, t) });
    } finally {
      setApplying(false);
    }
  }

  async function cancelConversion(conversion: NamingConversion) {
    if (!session) return;
    try {
      await api<NamingConversion>(`/naming/conversions/${conversion.id}/cancel`, {
        method: "POST",
        csrfToken: session.csrf_token,
      });
      setCancelTarget(null);
      await queryClient.invalidateQueries({ queryKey: ["naming-conversions"] });
      toast.success(t("naming.cancelRequested"));
    } catch (error) {
      toast.danger(t("common.error"), { description: namingErrorText(error, t) });
    }
  }

  async function deleteConversion(conversion: NamingConversion) {
    if (!session) return;
    try {
      await api<void>(`/naming/conversions/${conversion.id}`, {
        method: "DELETE",
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["naming-conversions"] });
      toast.success(t("naming.historyDeleted"));
    } catch (error) {
      toast.danger(t("common.error"), { description: namingErrorText(error, t) });
    }
  }

  return (
    <div className="grid min-w-0 gap-5">
      <PageHeader
        showDescription
        description={t("naming.description")}
        title={t("naming.title")}
        actions={
          <Button
            isDisabled={hasValidationErrors || draft.download_roots.length === 0 || Boolean(activeConversion)}
            isPending={scanning}
            variant="primary"
            onPress={() => void scanPreview()}
          >
            <Scan aria-hidden="true" size={17} />
            {t("naming.scanAndReview")}
          </Button>
        }
      />

      {activeConversion ? (
        <Alert status="accent">
          <Alert.Indicator>
            <Refresh aria-hidden="true" className={activeConversion.status === "running" ? "animate-spin" : ""} size={18} />
          </Alert.Indicator>
          <Alert.Content>
            <Alert.Title>{t("naming.conversionActive")}</Alert.Title>
            <Alert.Description>
              {t("naming.conversionActiveBody")}
            </Alert.Description>
          </Alert.Content>
        </Alert>
      ) : null}

      <ExternalChangeAlert
        visible={externalChange}
        onKeepEditing={() => setBaselineRevision(current.revision)}
        onReload={() => {
          setDraft(normalizeNaming(current.naming));
          setBaselineRevision(current.revision);
        }}
      />

      <Tabs
        aria-label={t("naming.title")}
        className="naming-tabs min-w-0"
        defaultSelectedKey="structure"
        variant="secondary"
      >
        <Tabs.List>
          <Tabs.Tab id="structure">
            <FolderCog aria-hidden="true" size={16} />
            {t("naming.structureTab")}
            <Tabs.Indicator />
          </Tabs.Tab>
          <Tabs.Tab id="templates">
            <Braces aria-hidden="true" size={16} />
            {t("naming.templatesTab")}
            <Tabs.Indicator />
          </Tabs.Tab>
          <Tabs.Tab id="history">
            <History aria-hidden="true" size={16} />
            {t("naming.historyTab")}
            <Tabs.Indicator />
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel className="grid min-w-0 gap-5 pt-5" id="structure">
          <FormSurface className="grid gap-4">
            <SectionHeading
              icon={FolderOpen}
              title={t("naming.downloadRoots")}
              description={t("naming.downloadRootsHint")}
              action={
                <Button size="sm" variant="outline" onPress={addDownloadRoot}>
                  <FolderPlus aria-hidden="true" size={16} />
                  {t("naming.addRoot")}
                </Button>
              }
            />
            {draft.download_roots.length ? (
              <div className="grid gap-3">
                {draft.download_roots.map((root, index) => (
                  <div
                    className="grid min-w-0 grid-cols-[minmax(0,1fr)_auto] items-end gap-2"
                    key={`download-root-${index}`}
                  >
                    <RemotePathField
                      errorMessage={
                        rootProblems[index]
                          ? t(`naming.validation.${rootProblems[index]}Root`)
                          : undefined
                      }
                      icon={Folder}
                      isInvalid={rootProblems[index] !== null}
                      label={t("naming.downloadRootNumber", { number: index + 1 })}
                      selector={{ kind: "directory", scope: "host", value_mode: "absolute" }}
                      value={root}
                      onChange={(value) =>
                        updateDraft((currentDraft) => ({
                          ...currentDraft,
                          download_roots: currentDraft.download_roots.map((item, itemIndex) =>
                            itemIndex === index ? value : item,
                          ),
                        }))
                      }
                    />
                    <Tooltip>
                      <Button
                        isIconOnly
                        aria-label={t("naming.removeRoot", { number: index + 1 })}
                        className="size-11 min-w-11 text-danger"
                        variant="ghost"
                        onPress={() =>
                          updateDraft((currentDraft) => ({
                            ...currentDraft,
                            download_roots: currentDraft.download_roots.filter(
                              (_, itemIndex) => itemIndex !== index,
                            ),
                          }))
                        }
                      >
                        <Trash aria-hidden="true" size={18} />
                      </Button>
                      <Tooltip.Content>{t("naming.removeRoot", { number: index + 1 })}</Tooltip.Content>
                    </Tooltip>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyPanel
                title={t("naming.noRoots")}
                description={t("naming.noRootsHint")}
              />
            )}
          </FormSurface>

          <div className="grid gap-5 xl:grid-cols-2">
            <FormSurface className="grid content-start gap-3">
              <SectionHeading
                icon={Settings}
                title={t("naming.layoutOptions")}
                description={t("naming.layoutOptionsHint")}
              />
              <FormSwitchField
                icon={CalendarStats}
                isSelected={draft.group_by_year}
                label={t("naming.groupByYear")}
                description={t("naming.groupByYearHint")}
                onChange={(selected) =>
                  updateDraft((value) => ({
                    ...value,
                    group_by_year: selected,
                    group_by_month: selected ? value.group_by_month : false,
                  }))
                }
              />
              <FormSwitchField
                icon={CalendarMonth}
                isDisabled={!draft.group_by_year}
                isSelected={draft.group_by_month}
                label={t("naming.groupByMonth")}
                description={t("naming.groupByMonthHint")}
                onChange={(selected) =>
                  updateDraft((value) => ({ ...value, group_by_month: selected }))
                }
              />
              <FormSwitchField
                icon={Files}
                isSelected={draft.mix_posts}
                label={t("naming.mixWorks")}
                description={t("naming.mixWorksHint")}
                onChange={(selected) =>
                  updateDraft((value) => ({ ...value, mix_posts: selected }))
                }
              />
              <FormSwitchField
                icon={ListNumbers}
                isSelected={draft.sequential_filename}
                label={t("naming.sequentialFiles")}
                description={t("naming.sequentialFilesHint")}
                onChange={(selected) =>
                  updateDraft((value) => ({ ...value, sequential_filename: selected }))
                }
              />
              <ChipListField
                icon={Tags}
                label={t("naming.sequentialExclusions")}
                description={t("naming.sequentialExclusionsHint")}
                placeholder=".zip, .psd, .mp4"
                values={draft.sequential_filename_excludes}
                onChange={(values) =>
                  updateDraft((value) => ({
                    ...value,
                    sequential_filename_excludes: values,
                  }))
                }
              />
            </FormSurface>

            <FormSurface className="grid content-start gap-4">
              <SectionHeading
                icon={Archive}
                title={t("naming.internalStructure")}
                description={t("naming.internalStructureHint")}
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  icon={Folder}
                  isInvalid={invalidRelativePath(draft.post_structure.attachments)}
                  label={t("naming.attachmentsDirectory")}
                  value={draft.post_structure.attachments}
                  onChange={(value) => updateStructure("attachments", value)}
                />
                <FormField
                  icon={Folder}
                  isInvalid={invalidRelativePath(draft.post_structure.revisions)}
                  label={t("naming.revisionsDirectory")}
                  value={draft.post_structure.revisions}
                  onChange={(value) => updateStructure("revisions", value)}
                />
                <FormField
                  icon={FileDescription}
                  isInvalid={invalidRelativePath(draft.post_structure.content)}
                  label={t("naming.contentFile")}
                  value={draft.post_structure.content}
                  onChange={(value) => updateStructure("content", value)}
                />
                <FormField
                  icon={FileCode}
                  isInvalid={invalidRelativePath(draft.post_structure.external_links)}
                  label={t("naming.externalLinksFile")}
                  value={draft.post_structure.external_links}
                  onChange={(value) => updateStructure("external_links", value)}
                />
              </div>
            </FormSurface>
          </div>
        </Tabs.Panel>

        <Tabs.Panel className="min-w-0 pt-5" id="templates">
          <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
            <FormSurface className="grid content-start gap-5">
              <SectionHeading
                icon={Braces}
                title={t("naming.templateFields")}
                description={t("naming.templateFieldsHint")}
              />
              <TemplateField
                allowed={creatorVariables}
                label={t("naming.creatorTemplate")}
                problem={invalidTemplate(draft.creator_dirname_format, creatorVariables)}
                value={draft.creator_dirname_format}
                onChange={(value) =>
                  updateDraft((currentDraft) => ({
                    ...currentDraft,
                    creator_dirname_format: value,
                  }))
                }
              />
              <TemplateField
                allowed={workVariables}
                label={t("naming.workTemplate")}
                problem={invalidTemplate(draft.post_dirname_format, workVariables)}
                value={draft.post_dirname_format}
                onChange={(value) =>
                  updateDraft((currentDraft) => ({
                    ...currentDraft,
                    post_dirname_format: value,
                  }))
                }
              />
              <TemplateField
                allowed={revisionVariables}
                label={t("naming.revisionTemplate")}
                problem={invalidTemplate(draft.revision_dirname_format, revisionVariables)}
                value={draft.revision_dirname_format}
                onChange={(value) =>
                  updateDraft((currentDraft) => ({
                    ...currentDraft,
                    revision_dirname_format: value,
                  }))
                }
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <TemplateField
                  allowed={dateVariables}
                  label={t("naming.yearTemplate")}
                  problem={invalidTemplate(draft.year_dirname_format, dateVariables)}
                  value={draft.year_dirname_format}
                  onChange={(value) =>
                    updateDraft((currentDraft) => ({
                      ...currentDraft,
                      year_dirname_format: value,
                    }))
                  }
                />
                <TemplateField
                  allowed={dateVariables}
                  label={t("naming.monthTemplate")}
                  problem={invalidTemplate(draft.month_dirname_format, dateVariables)}
                  value={draft.month_dirname_format}
                  onChange={(value) =>
                    updateDraft((currentDraft) => ({
                      ...currentDraft,
                      month_dirname_format: value,
                    }))
                  }
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <TemplateField
                  automatic
                  allowed={workVariables}
                  label={t("naming.primaryFileTemplate")}
                  problem={invalidTemplate(draft.post_structure.file, workVariables)}
                  value={draft.post_structure.file}
                  onChange={(value) => updateStructure("file", value)}
                />
                <TemplateField
                  automatic
                  allowed={workVariables}
                  label={t("naming.attachmentFileTemplate")}
                  problem={invalidTemplate(draft.filename_format, workVariables)}
                  value={draft.filename_format}
                  onChange={(value) =>
                    updateDraft((currentDraft) => ({
                      ...currentDraft,
                      filename_format: value,
                    }))
                  }
                />
              </div>
            </FormSurface>

            <div className="grid content-start gap-5">
              <FormSurface className="grid gap-3">
                <SectionHeading
                  icon={InfoCircle}
                  title={t("naming.availableVariables")}
                  description={t("naming.availableVariablesHint")}
                />
                <VariableGroup label={t("naming.creatorVariables")} values={creatorVariables} />
                <VariableGroup label={t("naming.workVariables")} values={workVariables} />
                <VariableGroup label={t("naming.revisionVariables")} values={["revision_id"]} />
                <VariableGroup label={t("naming.dateVariables")} values={dateVariables} />
                <p className="text-xs leading-5 text-muted">
                  {t("naming.automaticVariableHint")} <InlineCode>{"{}"}</InlineCode>
                </p>
              </FormSurface>
              <Surface
                className="grid gap-3 rounded-lg border border-border p-4"
                variant="secondary"
              >
                <SectionHeading
                  icon={FolderOpen}
                  title={t("naming.directoryPreview")}
                  description={t("naming.directoryPreviewHint")}
                />
                <div
                  aria-label={t("naming.directoryPreview")}
                  className="naming-tree max-h-[28rem] overflow-auto rounded-lg border border-border bg-surface p-3"
                  role="tree"
                  tabIndex={0}
                >
                  {tree.map((entry, index) => {
                    const EntryIcon = entry.kind === "folder" ? Folder : File;
                    return (
                      <div
                        className="flex min-w-max items-center gap-2 py-1.5 text-sm"
                        key={`${entry.depth}:${entry.name}:${index}`}
                        role="treeitem"
                        style={{ paddingInlineStart: `${entry.depth * 1.25}rem` }}
                      >
                        {entry.depth ? (
                          <ChevronRight aria-hidden="true" className="shrink-0 text-muted" size={14} />
                        ) : null}
                        <EntryIcon
                          aria-hidden="true"
                          className={entry.kind === "folder" ? "text-accent" : "text-muted"}
                          size={16}
                        />
                        <code className="max-w-[28rem] truncate" title={entry.name}>
                          {entry.name}
                        </code>
                      </div>
                    );
                  })}
                </div>
              </Surface>
            </div>
          </div>
        </Tabs.Panel>

        <Tabs.Panel className="min-w-0 pt-5" id="history">
          <ConversionHistory
            conversions={sortedConversions}
            locale={i18n.language}
            sortDescriptor={historySort}
            onCancel={setCancelTarget}
            onDelete={(conversion) => void deleteConversion(conversion)}
            onSortChange={setHistorySort}
          />
        </Tabs.Panel>
      </Tabs>

      {hasValidationErrors ? (
        <Alert status="danger">
          <Alert.Indicator>
            <AlertTriangle aria-hidden="true" size={18} />
          </Alert.Indicator>
          <Alert.Content>
            <Alert.Title>{t("naming.validation.title")}</Alert.Title>
            <Alert.Description>{t("naming.validation.body")}</Alert.Description>
          </Alert.Content>
        </Alert>
      ) : null}

      <PreviewModal
        applying={applying}
        convertExisting={convertExisting}
        preview={preview}
        selected={selectedCreators}
        onApply={() => void applyPreview()}
        onConvertChange={setConvertExisting}
        onOpenChange={(open) => !open && setPreview(null)}
        onSelectedChange={setSelectedCreators}
      />

      <FormModal
        open={cancelTarget !== null}
        size="md"
        title={t("naming.cancelTitle")}
        actions={
          <>
            <Button variant="ghost" onPress={() => setCancelTarget(null)}>
              <X aria-hidden="true" size={17} />
              {t("common.cancel")}
            </Button>
            <Button
              variant="danger"
              onPress={() => cancelTarget && void cancelConversion(cancelTarget)}
            >
              <Restore aria-hidden="true" size={17} />
              {t("naming.cancelAndRollback")}
            </Button>
          </>
        }
        onOpenChange={(open) => !open && setCancelTarget(null)}
      >
        <p className="text-sm leading-6 text-muted">{t("naming.cancelBody")}</p>
      </FormModal>
    </div>
  );
}

function SectionHeading({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: typeof Folder;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex min-w-0 flex-col justify-between gap-3 sm:flex-row sm:items-start">
      <div className="flex min-w-0 items-start gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent-soft-foreground">
          <Icon aria-hidden="true" size={18} stroke={1.8} />
        </span>
        <div className="min-w-0">
          <h2 className="font-semibold text-foreground">{title}</h2>
          <p className="mt-1 text-xs leading-5 text-muted">{description}</p>
        </div>
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

function TemplateField({
  label,
  value,
  allowed,
  problem,
  automatic = false,
  onChange,
}: {
  label: string;
  value: string;
  allowed: readonly string[];
  problem: string | null;
  automatic?: boolean;
  onChange: (value: string) => void;
}) {
  const { t } = useTranslation();
  const errorMessage =
    problem === "empty"
      ? t("naming.validation.empty")
      : problem === "separator"
        ? t("naming.validation.separator")
        : problem === "braces"
          ? t("naming.validation.braces")
          : problem
            ? t("naming.validation.unknownVariable", { variable: problem })
            : undefined;
  const hint = automatic
    ? t("naming.templateAutomaticHint")
    : t("naming.templateVariablesHint", {
        variables: allowed.map((name) => `{${name}}`).join(", "),
      });
  return (
    <FormField
      description={hint}
      errorMessage={errorMessage}
      icon={Braces}
      inputClassName="font-mono text-[0.8125rem]"
      isInvalid={problem !== null}
      label={label}
      value={value}
      onChange={onChange}
    />
  );
}

function VariableGroup({ label, values }: { label: string; values: readonly string[] }) {
  return (
    <div className="grid gap-2">
      <p className="text-xs font-semibold text-muted">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {values.map((value) => (
          <Chip key={value} size="sm" variant="soft">
            <code>{`{${value}}`}</code>
          </Chip>
        ))}
      </div>
    </div>
  );
}

function PreviewModal({
  preview,
  selected,
  convertExisting,
  applying,
  onSelectedChange,
  onConvertChange,
  onApply,
  onOpenChange,
}: {
  preview: NamingPreview | null;
  selected: Set<string>;
  convertExisting: boolean;
  applying: boolean;
  onSelectedChange: (value: Set<string>) => void;
  onConvertChange: (value: boolean) => void;
  onApply: () => void;
  onOpenChange: (open: boolean) => void;
}) {
  const { t } = useTranslation();
  if (!preview) return null;
  const selectable = preview.creators.filter((creator) => creator.selectable);
  const selectedItems = selectable.filter((creator) => selected.has(creator.key));
  const selectedFiles = selectedItems.reduce((total, creator) => total + creator.files, 0);
  const selectedWorks = selectedItems.reduce((total, creator) => total + creator.works, 0);
  const selectedBytes = selectedItems.reduce((total, creator) => total + creator.bytes, 0);
  const allSelected = selectable.length > 0 && selectedItems.length === selectable.length;

  function toggleCreator(creator: NamingCreatorPreview, isSelected: boolean) {
    const next = new Set(selected);
    if (isSelected) next.add(creator.key);
    else next.delete(creator.key);
    onSelectedChange(next);
  }

  return (
    <FormModal
      isWide
      open
      size="lg"
      title={t("naming.reviewTitle")}
      actions={
        <>
          <Button variant="ghost" onPress={() => onOpenChange(false)}>
            <X aria-hidden="true" size={17} />
            {t("common.cancel")}
          </Button>
          <Button
            isDisabled={
              preview.conflict_count > 0 ||
              (convertExisting && selected.size === 0)
            }
            isPending={applying}
            variant="primary"
            onPress={onApply}
          >
            <Check aria-hidden="true" size={17} />
            {convertExisting ? t("naming.applyAndConvert") : t("naming.saveWithoutConvert")}
          </Button>
        </>
      }
      onOpenChange={onOpenChange}
    >
      <div className="grid gap-4">
        <FormSwitchField
          icon={Refresh}
          isSelected={convertExisting}
          label={t("naming.convertExisting")}
          description={t("naming.convertExistingHint")}
          onChange={onConvertChange}
        />
        {!convertExisting ? (
          <Alert status="warning">
            <Alert.Indicator>
              <AlertTriangle aria-hidden="true" size={18} />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Title>{t("naming.saveOnlyTitle")}</Alert.Title>
              <Alert.Description>{t("naming.saveOnlyBody")}</Alert.Description>
            </Alert.Content>
          </Alert>
        ) : null}
        {preview.conflict_count ? (
          <Alert status="danger">
            <Alert.Indicator>
              <AlertTriangle aria-hidden="true" size={18} />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Title>
                {t("naming.conflictCount", { count: preview.conflict_count })}
              </Alert.Title>
              <Alert.Description>{t("naming.conflictBody")}</Alert.Description>
            </Alert.Content>
          </Alert>
        ) : null}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat label={t("naming.stats.creators")} value={selectedItems.length} />
          <Stat label={t("naming.stats.works")} value={selectedWorks} />
          <Stat label={t("naming.stats.files")} value={selectedFiles} />
          <Stat label={t("naming.stats.size")} value={formatBytes(selectedBytes)} />
        </div>
        {convertExisting && selectable.length ? (
          <BatchActionBar
            allVisibleSelected={allSelected}
            partiallySelected={selectedItems.length > 0 && !allSelected}
            selectedCount={selectedItems.length}
            onClear={() => onSelectedChange(new Set())}
            onSelectAll={(isSelected) =>
              onSelectedChange(
                new Set(isSelected ? selectable.map((creator) => creator.key) : []),
              )
            }
          >
            <Chip color={preview.skipped_count ? "warning" : "default"} size="sm" variant="soft">
              {t("naming.skippedCount", { count: preview.skipped_count })}
            </Chip>
          </BatchActionBar>
        ) : null}
        <DataTableFrame className="hidden md:block">
          <Table.Content
            aria-label={t("naming.reviewTitle")}
            className="table-fixed"
          >
            <Table.Header>
              <Table.Column aria-label={t("common.select")} className="w-12" />
              <Table.Column className="w-32" isRowHeader>
                <TableColumnLabel icon={User}>{t("naming.creator")}</TableColumnLabel>
              </Table.Column>
              <Table.Column>
                <TableColumnLabel icon={FolderOpen}>{t("naming.pathChange")}</TableColumnLabel>
              </Table.Column>
              <Table.Column className="w-20 text-right">
                <TableColumnLabel className="justify-end" icon={File}>{t("naming.stats.works")}</TableColumnLabel>
              </Table.Column>
              <Table.Column className="w-20 text-right">
                <TableColumnLabel className="justify-end" icon={Files}>{t("naming.stats.files")}</TableColumnLabel>
              </Table.Column>
              <Table.Column className="w-24">
                <TableColumnLabel icon={InfoCircle}>{t("naming.result")}</TableColumnLabel>
              </Table.Column>
            </Table.Header>
            <Table.Body>
              {preview.creators.map((creator) => (
                <Table.Row key={creator.key}>
                  <Table.Cell>
                    <SelectionCheckbox
                      isDisabled={!convertExisting || !creator.selectable}
                      isSelected={selected.has(creator.key)}
                      label={t("naming.selectCreator", { name: creator.name })}
                      onChange={(isSelected) => toggleCreator(creator, isSelected)}
                    />
                  </Table.Cell>
                  <Table.Cell className="font-medium">{creator.name}</Table.Cell>
                  <Table.Cell className="overflow-hidden">
                    <PathChange source={creator.source} target={creator.target} />
                  </Table.Cell>
                  <Table.Cell className="text-right tabular-nums">{creator.works}</Table.Cell>
                  <Table.Cell className="text-right tabular-nums">{creator.files}</Table.Cell>
                  <Table.Cell>
                    <PreviewResult creator={creator} />
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Content>
        </DataTableFrame>
        <div className="grid gap-3 md:hidden">
          {preview.creators.map((creator) => (
            <Surface className="grid gap-3 rounded-lg border border-border p-3" key={creator.key}>
              <div className="flex items-center gap-2">
                <SelectionCheckbox
                  isDisabled={!convertExisting || !creator.selectable}
                  isSelected={selected.has(creator.key)}
                  label={t("naming.selectCreator", { name: creator.name })}
                  onChange={(isSelected) => toggleCreator(creator, isSelected)}
                />
                <p className="min-w-0 flex-1 truncate font-semibold">{creator.name}</p>
                <PreviewResult creator={creator} />
              </div>
              <PathChange source={creator.source} target={creator.target} />
              <div className="flex flex-wrap gap-2 text-xs text-muted">
                <span>{t("naming.workCount", { count: creator.works })}</span>
                <span>{t("naming.fileCount", { count: creator.files })}</span>
                <span>{formatBytes(creator.bytes)}</span>
              </div>
            </Surface>
          ))}
        </div>
      </div>
    </FormModal>
  );
}

function PreviewResult({ creator }: { creator: NamingCreatorPreview }) {
  const { t } = useTranslation();
  if (creator.conflicts?.length) {
    return <Chip color="danger" size="sm" variant="soft">{t("naming.conflict")}</Chip>;
  }
  if (!creator.selectable) {
    return <Chip size="sm" variant="soft">{t("naming.noChanges")}</Chip>;
  }
  return <Chip color="success" size="sm" variant="soft">{t("naming.ready")}</Chip>;
}

function PathChange({ source, target }: { source: string; target: string }) {
  const sourceLabel = pathTail(source);
  const targetLabel = pathTail(target);
  return (
    <div className="grid min-w-0 max-w-full gap-1 overflow-hidden">
      <InlineCode className="block w-full max-w-full truncate" title={source}>{sourceLabel}</InlineCode>
      <div className="flex items-center gap-2 text-muted">
        <ChevronRight aria-hidden="true" size={14} />
        <InlineCode className="block min-w-0 max-w-full flex-1 truncate" title={target}>{targetLabel}</InlineCode>
      </div>
    </div>
  );
}

function pathTail(value: string): string {
  return value.split(/[\\/]/u).filter(Boolean).at(-1) ?? value;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-3">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 truncate font-semibold tabular-nums text-foreground" title={String(value)}>
        {value}
      </p>
    </div>
  );
}

function ConversionHistory({
  conversions,
  locale,
  sortDescriptor,
  onSortChange,
  onCancel,
  onDelete,
}: {
  conversions: NamingConversion[];
  locale: string;
  sortDescriptor: SortDescriptor;
  onSortChange: (value: SortDescriptor) => void;
  onCancel: (value: NamingConversion) => void;
  onDelete: (value: NamingConversion) => void;
}) {
  const { t } = useTranslation();
  if (!conversions.length) {
    return <EmptyPanel title={t("naming.noHistory")} description={t("naming.noHistoryHint")} />;
  }
  return (
    <>
      <DataTableFrame className="hidden md:block">
        <Table.Content
          aria-label={t("naming.historyTab")}
          sortDescriptor={sortDescriptor}
          onSortChange={onSortChange}
        >
          <Table.Header>
            <SortableColumn icon={CalendarStats} id="created_at" isRowHeader>
              {t("naming.startedAt")}
            </SortableColumn>
            <SortableColumn icon={Refresh} id="status">
              {t("common.status")}
            </SortableColumn>
            <Table.Column>
              <TableColumnLabel icon={Users}>{t("naming.stats.creators")}</TableColumnLabel>
            </Table.Column>
            <Table.Column>
              <TableColumnLabel icon={Files}>{t("naming.progress")}</TableColumnLabel>
            </Table.Column>
            <Table.Column className="text-right">
              <TableColumnLabel className="justify-end" icon={Settings}>
                {t("common.actions")}
              </TableColumnLabel>
            </Table.Column>
          </Table.Header>
          <Table.Body>
            {conversions.map((conversion) => (
              <Table.Row key={conversion.id}>
                <Table.Cell>{formatDateTime(conversion.created_at, locale)}</Table.Cell>
                <Table.Cell><ConversionStatus status={conversion.status} /></Table.Cell>
                <Table.Cell className="tabular-nums">{conversion.selected_creators.length}</Table.Cell>
                <Table.Cell>
                  <ConversionProgress conversion={conversion} />
                </Table.Cell>
                <Table.Cell className="text-right">
                  <ConversionActions conversion={conversion} onCancel={onCancel} onDelete={onDelete} />
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Content>
      </DataTableFrame>
      <div className="grid gap-3 md:hidden">
        {conversions.map((conversion) => (
          <Surface className="grid gap-3 rounded-lg border border-border p-3" key={conversion.id}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold">{formatDateTime(conversion.created_at, locale)}</p>
                <p className="mt-1 text-xs text-muted">
                  {t("naming.selectedCreatorCount", { count: conversion.selected_creators.length })}
                </p>
              </div>
              <ConversionStatus status={conversion.status} />
            </div>
            <ConversionProgress conversion={conversion} />
            <ConversionActions conversion={conversion} onCancel={onCancel} onDelete={onDelete} />
          </Surface>
        ))}
      </div>
    </>
  );
}

function ConversionStatus({ status }: { status: NamingConversion["status"] }) {
  const { t } = useTranslation();
  const color =
    status === "completed"
      ? "success"
      : status === "failed"
        ? "danger"
        : status === "cancelled"
          ? "warning"
          : status === "preview"
            ? "default"
            : "accent";
  return (
    <Chip color={color} size="sm" variant="soft">
      {t(`naming.statuses.${status}`)}
    </Chip>
  );
}

function ConversionProgress({ conversion }: { conversion: NamingConversion }) {
  const { t } = useTranslation();
  const progress = conversion.progress ?? {
    completed_operations: 0,
    total_operations: 0,
    current_creator: null,
  };
  const percent = progress.total_operations
    ? (progress.completed_operations / progress.total_operations) * 100
    : conversion.status === "completed"
      ? 100
      : 0;
  return (
    <div className="grid min-w-[10rem] gap-1.5">
      <ProgressBar
        aria-label={t("naming.progress")}
        isIndeterminate={["queued", "rolling_back"].includes(conversion.status)}
        value={percent}
      >
        <ProgressBar.Track>
          <ProgressBar.Fill />
        </ProgressBar.Track>
      </ProgressBar>
      <span className="text-xs tabular-nums text-muted">
        {progress.completed_operations}/{progress.total_operations}
      </span>
      {conversion.error ? (
        <span className="line-clamp-2 text-xs text-danger" title={conversion.error}>
          {conversion.error}
        </span>
      ) : null}
    </div>
  );
}

function ConversionActions({
  conversion,
  onCancel,
  onDelete,
}: {
  conversion: NamingConversion;
  onCancel: (value: NamingConversion) => void;
  onDelete: (value: NamingConversion) => void;
}) {
  const { t } = useTranslation();
  const active = activeConversionStatuses.has(conversion.status);
  return (
    <div className="flex justify-end gap-2">
      {active ? (
        <Button size="sm" variant="danger-soft" onPress={() => onCancel(conversion)}>
          <PlayerStop aria-hidden="true" size={16} />
          {t("common.cancel")}
        </Button>
      ) : (
        <Tooltip>
          <Button
            isIconOnly
            aria-label={t("naming.deleteHistory")}
            className="size-10 min-w-10 text-danger"
            size="sm"
            variant="ghost"
            onPress={() => onDelete(conversion)}
          >
            <Trash aria-hidden="true" size={17} />
          </Button>
          <Tooltip.Content>{t("naming.deleteHistory")}</Tooltip.Content>
        </Tooltip>
      )}
    </div>
  );
}

function namingErrorText(error: unknown, t: ReturnType<typeof useTranslation>["t"]): string {
  if (error instanceof ApiError) {
    if (error.status === 409) return t("naming.errors.stale");
    if (error.status === 422) return t("naming.errors.invalid");
  }
  return errorText(error);
}
