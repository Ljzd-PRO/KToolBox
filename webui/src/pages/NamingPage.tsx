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
  IconDatabaseImport as DatabaseImport,
  IconDeviceFloppy as Save,
  IconFile as File,
  IconFileCode as FileCode,
  IconFileDescription as FileDescription,
  IconFileTypeTxt as FileTypeEnv,
  IconFiles as Files,
  IconFolder as Folder,
  IconFolderCog as FolderCog,
  IconFolderDown as FolderOutput,
  IconFolderOpen as FolderOpen,
  IconFolderPlus as FolderPlus,
  IconHistory as History,
  IconInfoCircle as InfoCircle,
  IconListNumbers as ListNumbers,
  IconListCheck as ListCheck,
  IconPlayerPause as PlayerPause,
  IconPlayerPlay as PlayerPlay,
  IconPlayerStop as PlayerStop,
  IconRefresh as Refresh,
  IconRestore as Restore,
  IconScan as Scan,
  IconSourceCode as SourceCode,
  IconSettings as Settings,
  IconTags as Tags,
  IconTrash as Trash,
  IconUser as User,
  IconUsers as Users,
  IconX as X,
} from "@tabler/icons-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import { ExternalChangeAlert } from "../components/ExternalChangeAlert";
import {
  LegacyConfigEditor,
  type LegacyConfigEditorIssue,
} from "../components/LegacyConfigEditor";
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
  NamingLayoutVersion,
  NamingLegacyContext,
  NamingPreview,
  NamingSourceParse,
  ProjectNamingConfiguration,
  StartupNotice,
} from "../types";

type NamingDraft = Required<
  Omit<
    ProjectNamingConfiguration,
    "post_structure" | "sequential_filename_excludes"
  >
> & {
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
const activeConversionStatuses = new Set([
  "queued",
  "running",
  "pause_requested",
  "paused",
  "rolling_back",
]);
const legacyEnvSample = `# KToolBox v0 naming layout
KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{title}"
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS="attachments"
KTOOLBOX_JOB__POST_STRUCTURE__FILE="{id}_{}"
KTOOLBOX_JOB__FILENAME_FORMAT="{}"
KTOOLBOX_JOB__GROUP_BY_YEAR=false
`;
const namingTomlSample = `[naming]
creator_dirname_format = "{creator_name} [{service}-{creator_id}]"
post_dirname_format = "{title}"
revision_dirname_format = "{revision_id}"
filename_format = "{}"

[naming.post_structure]
attachments = "attachments"
content = "content.txt"
external_links = "external_links.txt"
file = "{id}_{}"
revisions = "revisions"
`;

function normalizeNaming(value: ProjectNamingConfiguration): NamingDraft {
  return {
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

function structureKey(value: NamingDraft | ProjectNamingConfiguration): string {
  const naming = normalizeNaming(value);
  return JSON.stringify({
    mix_posts: naming.mix_posts,
    sequential_filename: naming.sequential_filename,
    sequential_filename_excludes: naming.sequential_filename_excludes,
    group_by_year: naming.group_by_year,
    group_by_month: naming.group_by_month,
    post_structure: {
      attachments: naming.post_structure.attachments,
      content: naming.post_structure.content,
      external_links: naming.post_structure.external_links,
      revisions: naming.post_structure.revisions,
    },
  });
}

function templateKey(value: NamingDraft | ProjectNamingConfiguration): string {
  const naming = normalizeNaming(value);
  return JSON.stringify({
    creator_dirname_format: naming.creator_dirname_format,
    post_dirname_format: naming.post_dirname_format,
    revision_dirname_format: naming.revision_dirname_format,
    filename_format: naming.filename_format,
    year_dirname_format: naming.year_dirname_format,
    month_dirname_format: naming.month_dirname_format,
    primary_file: naming.post_structure.file,
  });
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedTab, setSelectedTabState] = useState(() =>
    namingTabFromSearchParams(searchParams),
  );
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
  const legacyContextQuery = useQuery({
    queryKey: ["naming-legacy-context"],
    queryFn: () => api<NamingLegacyContext>("/naming/legacy-context"),
  });
  const layoutVersionsQuery = useQuery({
    queryKey: ["naming-layout-versions"],
    queryFn: () => api<NamingLayoutVersion[]>("/naming/layout-versions"),
  });
  const noticesQuery = useQuery({
    queryKey: ["startup-notices"],
    queryFn: () => api<StartupNotice[]>("/startup-notices"),
  });
  const [draft, setDraft] = useState<NamingDraft | null>(null);
  const [baselineRevision, setBaselineRevision] = useState("");
  const [structureBaseline, setStructureBaseline] = useState("");
  const [templateBaseline, setTemplateBaseline] = useState("");
  const [defaultOutput, setDefaultOutput] = useState("");
  const [defaultOutputBaseline, setDefaultOutputBaseline] = useState("");
  const [legacyRoots, setLegacyRoots] = useState<string[] | null>(null);
  const [sourceMode, setSourceMode] = useState<"project_layout" | "pasted_config">(
    "project_layout",
  );
  const [selectedVersionIds, setSelectedVersionIds] = useState<Set<string>>(
    new Set(),
  );
  const [pastedFormat, setPastedFormat] = useState<"env" | "toml">("env");
  const [pastedDrafts, setPastedDrafts] = useState({ env: "", toml: "" });
  const [parsedSource, setParsedSource] = useState<NamingSourceParse | null>(null);
  const [parsingSource, setParsingSource] = useState(false);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [sourceIssues, setSourceIssues] = useState<LegacyConfigEditorIssue[]>([]);
  const [preview, setPreview] = useState<NamingPreview | null>(null);
  const [selectedCreators, setSelectedCreators] = useState<Set<string>>(new Set());
  const [scanning, setScanning] = useState(false);
  const [applying, setApplying] = useState(false);
  const [savingSection, setSavingSection] = useState<"structure" | "templates" | null>(null);
  const [historySort, setHistorySort] = useState<SortDescriptor>({
    column: "created_at",
    direction: "descending",
  });
  const [cancelTarget, setCancelTarget] = useState<NamingConversion | null>(null);
  const [dismissedLayoutVersion, setDismissedLayoutVersion] = useState<string | null>(null);

  const remoteNamingRevision = realtime?.revisions.naming ?? 0;
  const current = namingQuery.data;
  const structureDirty =
    draft !== null &&
    (
      structureKey(draft) !== structureBaseline ||
      defaultOutput !== defaultOutputBaseline
    );
  const templatesDirty = draft !== null && templateKey(draft) !== templateBaseline;
  const dirty = structureDirty || templatesDirty;
  const externalChange =
    dirty && Boolean(baselineRevision) && current?.revision !== baselineRevision;
  const activeConversion = conversionsQuery.data?.find((item) =>
    activeConversionStatuses.has(item.status),
  );
  const layoutNotice = noticesQuery.data?.find(
    (notice) =>
      notice.kind === "legacy_layout_conversion" &&
      notice.id !== dismissedLayoutVersion,
  ) ?? null;

  useEffect(() => {
    if (!current) return;
    if (!draft || !dirty) {
      const timer = window.setTimeout(() => {
        const normalized = normalizeNaming(current.naming);
        setDraft(normalized);
        setBaselineRevision(current.revision);
        setStructureBaseline(structureKey(normalized));
        setTemplateBaseline(templateKey(normalized));
        setDefaultOutput(current.default_output);
        setDefaultOutputBaseline(current.default_output);
      }, 0);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [current, dirty, draft, remoteNamingRevision]);

  useEffect(() => {
    if (legacyRoots !== null || !legacyContextQuery.data) return;
    const timer = window.setTimeout(
      () => setLegacyRoots([...(legacyContextQuery.data?.roots ?? [])]),
      0,
    );
    return () => window.clearTimeout(timer);
  }, [legacyContextQuery.data, legacyRoots]);

  useEffect(() => {
    if (selectedVersionIds.size || !layoutVersionsQuery.data?.length) return;
    const latestOld = layoutVersionsQuery.data.find((version) => !version.is_current);
    if (!latestOld) return;
    const timer = window.setTimeout(
      () => setSelectedVersionIds(new Set([latestOld.id])),
      0,
    );
    return () => window.clearTimeout(timer);
  }, [layoutVersionsQuery.data, selectedVersionIds.size]);

  useEffect(() => {
    const syncFromHistory = () => {
      setSelectedTabState(
        namingTabFromSearchParams(new URLSearchParams(window.location.search)),
      );
    };
    window.addEventListener("popstate", syncFromHistory);
    return () => window.removeEventListener("popstate", syncFromHistory);
  }, []);

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
    const normalized = (legacyRoots ?? []).map((root) => root.trim());
    return normalized.map((root, index) =>
      !root
        ? "empty"
        : normalized.indexOf(root) !== index
          ? "duplicate"
          : null,
    );
  }, [legacyRoots]);
  const hasStructureErrors =
    pathProblems.length > 0 ||
    !defaultOutput.trim() ||
    Boolean(draft?.group_by_month && !draft.group_by_year);
  const hasTemplateErrors = templateProblems.length > 0;
  const tree = useMemo(() => (draft ? sampleTree(draft) : []), [draft]);
  const sourceReady =
    sourceMode === "project_layout"
      ? selectedVersionIds.size > 0
      : parsedSource !== null && parsedSource.format === pastedFormat;
  const workflowStep = activeConversion
    ? 4
    : preview
      ? 3
      : sourceReady && legacyRoots?.length && !rootProblems.some(Boolean)
        ? 3
        : sourceReady
          ? 2
          : 1;
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

  if (
    namingQuery.isLoading ||
    conversionsQuery.isLoading ||
    legacyContextQuery.isLoading ||
    layoutVersionsQuery.isLoading ||
    !draft ||
    !current ||
    legacyRoots === null
  ) {
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
    setLegacyRoots((value) => [...(value ?? []), ""]);
  }

  function updatePastedDraft(value: string) {
    setPastedDrafts((drafts) => ({ ...drafts, [pastedFormat]: value }));
    setParsedSource(null);
    setSourceError(null);
    setSourceIssues([]);
  }

  async function parsePastedSource() {
    if (!session || !pastedDrafts[pastedFormat].trim()) return;
    setParsingSource(true);
    setSourceError(null);
    setSourceIssues([]);
    try {
      const result = await api<NamingSourceParse>("/naming/source/parse", {
        method: "POST",
        body: {
          format: pastedFormat,
          content: pastedDrafts[pastedFormat],
        },
        csrfToken: session.csrf_token,
      });
      setParsedSource(result);
      setSourceIssues([]);
      toast.success(t("naming.workflow.parseSuccess"), {
        description: t("naming.workflow.parseSuccessHint", {
          count: result.recognized_fields.length,
        }),
      });
    } catch (error) {
      setParsedSource(null);
      const issues = sourceParseIssues(error, t);
      setSourceIssues(issues);
      setSourceError(issues[0]?.message ?? sourceParseErrorText(error, t));
    } finally {
      setParsingSource(false);
    }
  }

  async function saveSection(section: "structure" | "templates") {
    if (
      !session ||
      !draft ||
      (section === "structure" ? hasStructureErrors : hasTemplateErrors)
    ) return;
    const candidate = draft;
    const layoutChanged = section === "structure"
      ? structureKey(candidate) !== structureBaseline
      : templateKey(candidate) !== templateBaseline;
    setSavingSection(section);
    try {
      const result = await api<NamingConfigurationResponse>("/naming", {
        method: "PATCH",
        body: {
          section,
          naming: candidate,
          revision: baselineRevision,
          default_output: section === "structure" ? defaultOutput : undefined,
        },
        csrfToken: session.csrf_token,
      });
      queryClient.setQueryData(["naming"], result);
      setBaselineRevision(result.revision);
      if (section === "structure") {
        setStructureBaseline(structureKey(candidate));
        setDefaultOutput(result.default_output);
        setDefaultOutputBaseline(result.default_output);
      } else {
        setTemplateBaseline(templateKey(candidate));
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["naming-legacy-context"] }),
        queryClient.invalidateQueries({ queryKey: ["naming-layout-versions"] }),
        queryClient.invalidateQueries({ queryKey: ["startup-notices"] }),
      ]);
      toast.success(t(layoutChanged ? "naming.saved" : "naming.defaultOutputSaved"), {
        description: t(
          layoutChanged
            ? "naming.savedConversionHint"
            : "naming.defaultOutputSavedHint",
        ),
      });
    } catch (error) {
      toast.danger(t("common.error"), { description: namingErrorText(error, t) });
    } finally {
      setSavingSection(null);
    }
  }

  async function scanPreview() {
    if (
      !session ||
      !legacyRoots ||
      !sourceReady ||
      rootProblems.some(Boolean) ||
      legacyRoots.length === 0
    ) return;
    const roots = legacyRoots;
    const source = sourceMode === "project_layout"
      ? {
          kind: "project_layout" as const,
          version_ids: [...selectedVersionIds],
        }
      : parsedSource
        ? {
            kind: "pasted_config" as const,
            format: parsedSource.format,
            naming: parsedSource.naming,
            digest: parsedSource.digest,
          }
        : null;
    if (!source) return;
    setScanning(true);
    try {
      const result = await api<NamingPreview>("/naming/preview", {
        method: "POST",
        body: {
          roots,
          source,
        },
        csrfToken: session.csrf_token,
      });
      setPreview(result);
      setSelectedCreators(
        new Set(result.creators.filter((creator) => creator.selectable).map((creator) => creator.key)),
      );
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
      await api<NamingConversion>("/naming/apply", {
        method: "POST",
        body: {
          preview_id: preview.id,
          selected_creators: [...selectedCreators],
        },
        csrfToken: session.csrf_token,
      });
      setPreview(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["naming"] }),
        queryClient.invalidateQueries({ queryKey: ["naming-conversions"] }),
        queryClient.invalidateQueries({ queryKey: ["startup-notices"] }),
      ]);
    } catch (error) {
      toast.danger(t("common.error"), { description: namingErrorText(error, t) });
    } finally {
      setApplying(false);
    }
  }

  function setSelectedTab(tab: string) {
    setSelectedTabState(tab as NamingTab);
    const next = new URLSearchParams(searchParams);
    if (tab === "structure") next.delete("tab");
    else next.set("tab", tab);
    setSearchParams(next, { replace: true });
  }

  function startAutomaticScan(notice?: StartupNotice) {
    const linkedVersion =
      typeof notice?.payload?.source_version_id === "string"
        ? notice.payload.source_version_id
        : null;
    if (linkedVersion) setSelectedVersionIds(new Set([linkedVersion]));
    setSourceMode("project_layout");
    setSelectedTabState("legacy");
    const next = new URLSearchParams(searchParams);
    next.delete("autostart");
    next.set("tab", "legacy");
    setSearchParams(next, { replace: true });
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

  async function pauseConversion(conversion: NamingConversion) {
    if (!session) return;
    try {
      await api<NamingConversion>(`/naming/conversions/${conversion.id}/pause`, {
        method: "POST",
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["naming-conversions"] });
    } catch (error) {
      toast.danger(t("common.error"), { description: namingErrorText(error, t) });
    }
  }

  async function resumeConversion(conversion: NamingConversion) {
    if (!session) return;
    try {
      await api<NamingConversion>(`/naming/conversions/${conversion.id}/resume`, {
        method: "POST",
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["naming-conversions"] });
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

  async function ignoreLayoutVersion(notice: StartupNotice) {
    if (!session) return;
    try {
      await api<StartupNotice>(`/startup-notices/${notice.id}/resolve`, {
        method: "POST",
        body: { action: "ignored" },
        csrfToken: session.csrf_token,
      });
      setDismissedLayoutVersion(notice.id);
      await queryClient.invalidateQueries({ queryKey: ["startup-notices"] });
      toast.success(t("naming.startup.ignored"));
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
          const normalized = normalizeNaming(current.naming);
          setDraft(normalized);
          setBaselineRevision(current.revision);
          setStructureBaseline(structureKey(normalized));
          setTemplateBaseline(templateKey(normalized));
          setDefaultOutput(current.default_output);
          setDefaultOutputBaseline(current.default_output);
        }}
      />

      <Tabs
        aria-label={t("naming.title")}
        className="naming-tabs min-w-0"
        selectedKey={selectedTab}
        variant="secondary"
        onSelectionChange={(key) => setSelectedTab(String(key))}
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
          <Tabs.Tab id="legacy">
            <DatabaseImport aria-hidden="true" size={16} />
            {t("naming.legacyTab")}
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
              icon={FolderOutput}
              title={t("naming.defaultOutputTitle")}
              description={t("naming.defaultOutputDescription")}
            />
            <RemotePathField
              description={
                <>
                  {t("naming.defaultOutputHint")}{" "}
                  {current.resolved_default_output ? (
                    <InlineCode>{current.resolved_default_output}</InlineCode>
                  ) : null}
                </>
              }
              errorMessage={!defaultOutput.trim() ? t("naming.validation.emptyRoot") : undefined}
              icon={FolderOutput}
              isInvalid={!defaultOutput.trim()}
              label={t("naming.defaultOutputLabel")}
              selector={{ kind: "directory", scope: "host", value_mode: "absolute" }}
              value={defaultOutput}
              onChange={setDefaultOutput}
            />
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
          <SectionSaveBar
            dirty={structureDirty}
            isDisabled={hasStructureErrors}
            isPending={savingSection === "structure"}
            label={t("naming.saveStructure")}
            onSave={() => void saveSection("structure")}
          />
        </Tabs.Panel>

        <Tabs.Panel className="grid min-w-0 gap-5 pt-5" id="templates">
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
          <SectionSaveBar
            dirty={templatesDirty}
            isDisabled={hasTemplateErrors}
            isPending={savingSection === "templates"}
            label={t("naming.saveTemplates")}
            onSave={() => void saveSection("templates")}
          />
        </Tabs.Panel>

        <Tabs.Panel className="grid min-w-0 gap-5 pt-5" id="legacy">
          <Alert status="accent">
            <Alert.Indicator>
              <DatabaseImport aria-hidden="true" size={18} />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Title>{t("naming.legacyTitle")}</Alert.Title>
              <Alert.Description>{t("naming.legacyDescription")}</Alert.Description>
            </Alert.Content>
          </Alert>

          <WorkflowSteps current={workflowStep} />

          <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.85fr)]">
            <FormSurface className="grid min-w-0 gap-4">
              <SectionHeading
                icon={SourceCode}
                title={t("naming.workflow.sourceTitle")}
                description={t("naming.workflow.sourceHint")}
              />
              <Tabs
                aria-label={t("naming.workflow.sourceTitle")}
                selectedKey={sourceMode}
                variant="secondary"
                onSelectionChange={(key) =>
                  setSourceMode(String(key) as typeof sourceMode)
                }
              >
                <Tabs.List className="grid grid-cols-2">
                  <Tabs.Tab id="project_layout">
                    <History aria-hidden="true" size={16} />
                    {t("naming.workflow.projectMode")}
                    <Tabs.Indicator />
                  </Tabs.Tab>
                  <Tabs.Tab id="pasted_config">
                    <FileCode aria-hidden="true" size={16} />
                    {t("naming.workflow.pastedMode")}
                    <Tabs.Indicator />
                  </Tabs.Tab>
                </Tabs.List>
                <Tabs.Panel className="grid gap-3 pt-4" id="project_layout">
                  <p className="text-xs leading-5 text-muted">
                    {t("naming.workflow.projectModeHint")}
                  </p>
                  {layoutVersionsQuery.data?.some((version) => !version.is_current) ? (
                    <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
                      {layoutVersionsQuery.data.map((version) => {
                        const selected = selectedVersionIds.has(version.id);
                        return (
                          <Surface
                            className="grid gap-2 rounded-lg border border-border p-3"
                            key={version.id}
                            variant={selected ? "secondary" : "default"}
                          >
                            <div className="flex min-w-0 items-center gap-3">
                              <SelectionCheckbox
                                isDisabled={version.is_current}
                                isSelected={selected}
                                label={t("naming.workflow.selectVersion", {
                                  date: formatDateTime(version.created_at, i18n.language),
                                })}
                                onChange={(isSelected) => {
                                  const next = new Set(selectedVersionIds);
                                  if (isSelected) next.add(version.id);
                                  else next.delete(version.id);
                                  setSelectedVersionIds(next);
                                }}
                              />
                              <div className="min-w-0 flex-1">
                                <p className="truncate text-sm font-semibold">
                                  {formatDateTime(version.created_at, i18n.language)}
                                </p>
                                <InlineCode className="mt-1 block w-fit max-w-full truncate">
                                  {version.revision.slice(0, 12)}
                                </InlineCode>
                              </div>
                              <Chip
                                color={version.is_current ? "success" : "default"}
                                size="sm"
                                variant="soft"
                              >
                                {t(
                                  version.is_current
                                    ? "naming.workflow.currentVersion"
                                    : "naming.workflow.previousVersion",
                                )}
                              </Chip>
                            </div>
                          </Surface>
                        );
                      })}
                    </div>
                  ) : (
                    <EmptyPanel
                      title={t("naming.workflow.noPreviousVersions")}
                      description={t("naming.workflow.noPreviousVersionsHint")}
                    />
                  )}
                </Tabs.Panel>
                <Tabs.Panel className="grid min-w-0 gap-4 pt-4" id="pasted_config">
                  <p className="text-xs leading-5 text-muted">
                    {t("naming.workflow.pastedModeHint")}
                  </p>
                  <Tabs
                    aria-label={t("naming.workflow.sourceFormat")}
                    selectedKey={pastedFormat}
                    variant="secondary"
                    onSelectionChange={(key) => {
                      setPastedFormat(String(key) as typeof pastedFormat);
                      setParsedSource(null);
                      setSourceError(null);
                      setSourceIssues([]);
                    }}
                  >
                    <Tabs.List className="grid grid-cols-2">
                      <Tabs.Tab id="env">
                        <FileTypeEnv aria-hidden="true" size={16} />
                        {t("naming.workflow.envFormat")}
                        <Tabs.Indicator />
                      </Tabs.Tab>
                      <Tabs.Tab id="toml">
                        <Braces aria-hidden="true" size={16} />
                        {t("naming.workflow.tomlFormat")}
                        <Tabs.Indicator />
                      </Tabs.Tab>
                    </Tabs.List>
                    <Tabs.Panel className="pt-3" id="env">
                      <LegacyConfigEditor
                        description={t("naming.workflow.editorPrivacy")}
                        format="env"
                        issues={sourceIssues}
                        label={t("naming.workflow.envEditor")}
                        placeholder={legacyEnvSample}
                        value={pastedDrafts.env}
                        onChange={updatePastedDraft}
                      />
                    </Tabs.Panel>
                    <Tabs.Panel className="pt-3" id="toml">
                      <LegacyConfigEditor
                        description={t("naming.workflow.editorPrivacy")}
                        format="toml"
                        issues={sourceIssues}
                        label={t("naming.workflow.tomlEditor")}
                        placeholder={namingTomlSample}
                        value={pastedDrafts.toml}
                        onChange={updatePastedDraft}
                      />
                    </Tabs.Panel>
                  </Tabs>
                  {sourceError ? (
                    <Alert status="danger">
                      <Alert.Indicator>
                        <AlertTriangle aria-hidden="true" size={18} />
                      </Alert.Indicator>
                      <Alert.Content>
                        <Alert.Title>{t("naming.workflow.parseFailed")}</Alert.Title>
                        <Alert.Description>{sourceError}</Alert.Description>
                      </Alert.Content>
                    </Alert>
                  ) : null}
                  {parsedSource ? (
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                      <Stat
                        label={t("naming.workflow.recognizedFields")}
                        value={parsedSource.recognized_fields.length}
                      />
                      <Stat
                        label={t("naming.workflow.defaultedFields")}
                        value={parsedSource.defaulted_fields.length}
                      />
                      <Stat
                        label={t("naming.workflow.differences")}
                        value={parsedSource.differences.length}
                      />
                      <Stat
                        label={t("naming.workflow.ignoredEntries")}
                        value={parsedSource.warnings.reduce(
                          (total, warning) => total + warning.count,
                          0,
                        )}
                      />
                    </div>
                  ) : null}
                  <div className="flex flex-wrap justify-end gap-2 border-t border-border pt-3">
                    <Button
                      variant="outline"
                      onPress={() =>
                        updatePastedDraft(
                          pastedFormat === "env" ? legacyEnvSample : namingTomlSample,
                        )
                      }
                    >
                      <FileCode aria-hidden="true" size={16} />
                      {t("naming.workflow.insertSample")}
                    </Button>
                    <Button
                      isDisabled={!pastedDrafts[pastedFormat].trim()}
                      isPending={parsingSource}
                      variant="primary"
                      onPress={() => void parsePastedSource()}
                    >
                      <ListCheck aria-hidden="true" size={16} />
                      {t("naming.workflow.parseSource")}
                    </Button>
                  </div>
                </Tabs.Panel>
              </Tabs>
            </FormSurface>

            <FormSurface className="grid min-w-0 content-start gap-4">
              <SectionHeading
                icon={FolderCog}
                title={t("naming.workflow.targetTitle")}
                description={t("naming.workflow.targetHint")}
              />
              <div className="flex flex-wrap items-center gap-2">
                <Chip color="success" size="sm" variant="soft">
                  {t("naming.workflow.currentTarget")}
                </Chip>
                <span className="text-xs text-muted">
                  {t("naming.workflow.targetRevision")}
                </span>
                <InlineCode>{current.revision.slice(0, 12)}</InlineCode>
              </div>
              <div
                aria-label={t("naming.directoryPreview")}
                className="naming-tree max-h-[26rem] overflow-auto rounded-lg border border-border bg-surface p-3"
                role="tree"
                tabIndex={0}
              >
                {tree.map((entry, index) => {
                  const EntryIcon = entry.kind === "folder" ? Folder : File;
                  return (
                    <div
                      className="flex min-w-max items-center gap-2 py-1.5 text-sm"
                      key={`target:${entry.depth}:${entry.name}:${index}`}
                      role="treeitem"
                      style={{ paddingInlineStart: `${entry.depth * 1.25}rem` }}
                    >
                      {entry.depth ? (
                        <ChevronRight
                          aria-hidden="true"
                          className="shrink-0 text-muted"
                          size={14}
                        />
                      ) : null}
                      <EntryIcon
                        aria-hidden="true"
                        className={entry.kind === "folder" ? "text-accent" : "text-muted"}
                        size={16}
                      />
                      <code className="max-w-[24rem] truncate" title={entry.name}>
                        {entry.name}
                      </code>
                    </div>
                  );
                })}
              </div>
            </FormSurface>
          </div>

          <FormSurface className="grid gap-4">
            <SectionHeading
              icon={FolderOpen}
              title={t("naming.legacyRoots")}
              description={t("naming.legacyRootsHint")}
              action={
                <Button size="sm" variant="outline" onPress={addDownloadRoot}>
                  <FolderPlus aria-hidden="true" size={16} />
                  {t("naming.addLegacyRoot")}
                </Button>
              }
            />
            {legacyRoots.length ? (
              <div className="grid gap-3">
                {legacyRoots.map((root, index) => (
                  <div
                    className="grid min-w-0 grid-cols-[minmax(0,1fr)_auto] items-end gap-2"
                    key={`legacy-root-${index}`}
                  >
                    <RemotePathField
                      errorMessage={
                        rootProblems[index]
                          ? t(`naming.validation.${rootProblems[index]}Root`)
                          : undefined
                      }
                      icon={Folder}
                      isInvalid={rootProblems[index] !== null}
                      label={t("naming.legacyRootNumber", { number: index + 1 })}
                      selector={{ kind: "directory", scope: "host", value_mode: "absolute" }}
                      value={root}
                      onChange={(value) =>
                        setLegacyRoots((roots) =>
                          (roots ?? []).map((item, itemIndex) =>
                            itemIndex === index ? value : item,
                          ),
                        )
                      }
                    />
                    <Tooltip>
                      <Button
                        isIconOnly
                        aria-label={t("naming.removeLegacyRoot", { number: index + 1 })}
                        className="size-11 min-w-11 text-danger"
                        variant="ghost"
                        onPress={() =>
                          setLegacyRoots((roots) =>
                            (roots ?? []).filter((_, itemIndex) => itemIndex !== index),
                          )
                        }
                      >
                        <Trash aria-hidden="true" size={18} />
                      </Button>
                      <Tooltip.Content>
                        {t("naming.removeLegacyRoot", { number: index + 1 })}
                      </Tooltip.Content>
                    </Tooltip>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyPanel
                title={t("naming.noLegacyRoots")}
                description={t("naming.noLegacyRootsHint")}
              />
            )}
            <div className="flex justify-end border-t border-border pt-4">
              <Button
                isDisabled={
                  !sourceReady ||
                  rootProblems.some(Boolean) ||
                  legacyRoots.length === 0 ||
                  Boolean(activeConversion)
                }
                isPending={scanning}
                variant="primary"
                onPress={() => void scanPreview()}
              >
                <Scan aria-hidden="true" size={17} />
                {t("naming.scanLegacyRoots")}
              </Button>
            </div>
          </FormSurface>

        </Tabs.Panel>

        <Tabs.Panel className="grid min-w-0 gap-5 pt-5" id="history">
          <section className="grid gap-3" aria-labelledby="naming-history-title">
            <div>
              <h2 className="text-lg font-semibold" id="naming-history-title">
                {t("naming.historyTab")}
              </h2>
              <p className="mt-1 text-sm text-muted">{t("naming.historyHint")}</p>
            </div>
            <ConversionHistory
              conversions={sortedConversions}
              locale={i18n.language}
              sortDescriptor={historySort}
              onCancel={setCancelTarget}
              onDelete={(conversion) => void deleteConversion(conversion)}
              onPause={(conversion) => void pauseConversion(conversion)}
              onResume={(conversion) => void resumeConversion(conversion)}
              onSortChange={setHistorySort}
            />
          </section>
        </Tabs.Panel>
      </Tabs>

      {selectedTab === "structure" && hasStructureErrors ? (
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

      {selectedTab === "templates" && hasTemplateErrors ? (
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
        preview={preview}
        selected={selectedCreators}
        onApply={() => void applyPreview()}
        onOpenChange={(open) => !open && setPreview(null)}
        onSelectedChange={setSelectedCreators}
      />

      <FormModal
        open={layoutNotice !== null}
        size="md"
        title={t("naming.startup.title")}
        actions={
          <>
            <Button
              variant="ghost"
              onPress={() => layoutNotice && void ignoreLayoutVersion(layoutNotice)}
            >
              <X aria-hidden="true" size={17} />
              {t("naming.startup.ignore")}
            </Button>
            <Button
              variant="primary"
              onPress={() => {
                if (layoutNotice) setDismissedLayoutVersion(layoutNotice.id);
                startAutomaticScan(layoutNotice ?? undefined);
              }}
            >
              <DatabaseImport aria-hidden="true" size={17} />
              {t("naming.startup.convert")}
            </Button>
          </>
        }
        onOpenChange={(open) => {
          if (!open && layoutNotice) setDismissedLayoutVersion(layoutNotice.id);
        }}
      >
        <div className="grid gap-4">
          <Alert status="accent">
            <Alert.Indicator>
              <DatabaseImport aria-hidden="true" size={18} />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Title>{t("naming.startup.heading")}</Alert.Title>
              <Alert.Description>{t("naming.startup.body")}</Alert.Description>
            </Alert.Content>
          </Alert>
          <p className="text-sm leading-6 text-muted">
            {t("naming.startup.versionHint")}
          </p>
        </div>
      </FormModal>

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

type NamingTab = "structure" | "templates" | "legacy" | "history";

function namingTabFromSearchParams(searchParams: URLSearchParams): NamingTab {
  const tab = searchParams.get("tab");
  return tab === "legacy" || tab === "templates" || tab === "history"
    ? tab
    : "structure";
}

function WorkflowSteps({ current }: { current: number }) {
  const { t } = useTranslation();
  const steps = [
    ["source", SourceCode],
    ["roots", FolderOpen],
    ["preview", Scan],
    ["convert", Refresh],
  ] as const;
  return (
    <ol
      aria-label={t("naming.workflow.title")}
      className="grid grid-cols-2 gap-2 sm:grid-cols-4"
    >
      {steps.map(([key, Icon], index) => {
        const number = index + 1;
        const completed = number < current;
        const active = number === current;
        return (
          <li
            aria-current={active ? "step" : undefined}
            className={[
              "flex min-w-0 items-center gap-2 rounded-lg border px-3 py-2.5 text-sm",
              active
                ? "border-accent bg-accent-soft text-accent-soft-foreground"
                : completed
                  ? "border-success/40 bg-success/10 text-foreground"
                  : "border-border bg-surface text-muted",
            ].join(" ")}
            key={key}
          >
            <span
              aria-hidden="true"
              className="grid size-7 shrink-0 place-items-center rounded-full bg-surface font-semibold tabular-nums"
            >
              {completed ? <Check size={15} /> : number}
            </span>
            <Icon aria-hidden="true" className="shrink-0" size={16} />
            <span className="min-w-0 truncate">
              {t(`naming.workflow.steps.${key}`)}
            </span>
          </li>
        );
      })}
    </ol>
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

function SectionSaveBar({
  dirty,
  isDisabled,
  isPending,
  label,
  onSave,
}: {
  dirty: boolean;
  isDisabled: boolean;
  isPending: boolean;
  label: string;
  onSave: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Surface
      className="flex flex-col gap-3 rounded-lg border border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
      variant="secondary"
    >
      <div className="flex min-w-0 items-center gap-2">
        <Chip color={dirty ? "warning" : "success"} size="sm" variant="soft">
          {t(dirty ? "naming.unsavedChanges" : "naming.changesSaved")}
        </Chip>
        <span className="text-xs leading-5 text-muted">{t("naming.saveSectionHint")}</span>
      </div>
      <Button
        className="w-full sm:w-auto"
        isDisabled={!dirty || isDisabled}
        isPending={isPending}
        variant="primary"
        onPress={onSave}
      >
        <Save aria-hidden="true" size={17} />
        {label}
      </Button>
    </Surface>
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
  applying,
  onSelectedChange,
  onApply,
  onOpenChange,
}: {
  preview: NamingPreview | null;
  selected: Set<string>;
  applying: boolean;
  onSelectedChange: (value: Set<string>) => void;
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
  const hasMoves = selectable.length > 0;

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
              (hasMoves && selected.size === 0)
            }
            isPending={applying}
            variant="primary"
            onPress={onApply}
          >
            <Check aria-hidden="true" size={17} />
            {hasMoves ? t("naming.applyAndConvert") : t("naming.completeReview")}
          </Button>
        </>
      }
      onOpenChange={onOpenChange}
    >
      <div className="grid gap-4">
        <p className="text-sm leading-6 text-muted">{t("naming.reviewDescription")}</p>
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
        {hasMoves ? (
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
                      isDisabled={!creator.selectable}
                      isSelected={selected.has(creator.key)}
                      label={t("naming.selectCreator", { name: creator.name })}
                      onChange={(isSelected) => toggleCreator(creator, isSelected)}
                    />
                  </Table.Cell>
                  <Table.Cell className="font-medium">{creator.name}</Table.Cell>
                  <Table.Cell className="overflow-hidden">
                    <PathChange
                      operations={creator.operations}
                      source={creator.source}
                      target={creator.target}
                    />
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
                  isDisabled={!creator.selectable}
                  isSelected={selected.has(creator.key)}
                  label={t("naming.selectCreator", { name: creator.name })}
                  onChange={(isSelected) => toggleCreator(creator, isSelected)}
                />
                <p className="min-w-0 flex-1 truncate font-semibold">{creator.name}</p>
                <PreviewResult creator={creator} />
              </div>
              <PathChange
                operations={creator.operations}
                source={creator.source}
                target={creator.target}
              />
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

function PathChange({
  operations,
  source,
  target,
}: {
  operations: number;
  source: string;
  target: string;
}) {
  const { t } = useTranslation();
  const sourceLabel = pathTail(source);
  const targetLabel = pathTail(target);
  if (source === target) {
    return (
      <div className="grid min-w-0 max-w-full gap-1 overflow-hidden">
        <InlineCode className="block w-full max-w-full truncate" title={source}>
          {sourceLabel}
        </InlineCode>
        <p className="truncate text-xs text-muted">
          {t("naming.internalMoves", { count: operations })}
        </p>
      </div>
    );
  }
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
  onPause,
  onResume,
}: {
  conversions: NamingConversion[];
  locale: string;
  sortDescriptor: SortDescriptor;
  onSortChange: (value: SortDescriptor) => void;
  onCancel: (value: NamingConversion) => void;
  onDelete: (value: NamingConversion) => void;
  onPause: (value: NamingConversion) => void;
  onResume: (value: NamingConversion) => void;
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
            <Table.Column>
              <TableColumnLabel icon={SourceCode}>
                {t("naming.workflow.historySource")}
              </TableColumnLabel>
            </Table.Column>
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
                <Table.Cell>
                  <ConversionSourceChip conversion={conversion} />
                </Table.Cell>
                <Table.Cell><ConversionStatus status={conversion.status} /></Table.Cell>
                <Table.Cell className="tabular-nums">{conversion.selected_creators.length}</Table.Cell>
                <Table.Cell>
                  <ConversionProgress conversion={conversion} />
                </Table.Cell>
                <Table.Cell className="text-right">
                  <ConversionActions
                    conversion={conversion}
                    onCancel={onCancel}
                    onDelete={onDelete}
                    onPause={onPause}
                    onResume={onResume}
                  />
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
            <ConversionSourceChip conversion={conversion} />
            <ConversionProgress conversion={conversion} />
            <ConversionActions
              conversion={conversion}
              onCancel={onCancel}
              onDelete={onDelete}
              onPause={onPause}
              onResume={onResume}
            />
          </Surface>
        ))}
      </div>
    </>
  );
}

function ConversionSourceChip({ conversion }: { conversion: NamingConversion }) {
  const { t } = useTranslation();
  const source = conversion.preview.source;
  const label =
    source?.kind === "pasted_config"
      ? t(`naming.workflow.sourceKinds.${source.format}`)
      : t("naming.workflow.sourceKinds.project");
  const detail =
    source?.kind === "pasted_config"
      ? t("naming.workflow.pastedSourceSummary", {
          digest: source.digest.slice(0, 12),
        })
      : t("naming.workflow.projectSourceSummary", {
          count: source?.kind === "project_layout" ? source.version_ids.length : 0,
        });
  return (
    <Tooltip>
      <Chip
        color={source?.kind === "pasted_config" ? "accent" : "default"}
        size="sm"
        variant="soft"
      >
        {label}
      </Chip>
      <Tooltip.Content>{detail}</Tooltip.Content>
    </Tooltip>
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
        isIndeterminate={["queued", "pause_requested", "rolling_back"].includes(conversion.status)}
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
  onPause,
  onResume,
}: {
  conversion: NamingConversion;
  onCancel: (value: NamingConversion) => void;
  onDelete: (value: NamingConversion) => void;
  onPause: (value: NamingConversion) => void;
  onResume: (value: NamingConversion) => void;
}) {
  const { t } = useTranslation();
  const active = activeConversionStatuses.has(conversion.status);
  return (
    <div className="flex justify-end gap-2">
      {active ? (
        <>
          {["queued", "running"].includes(conversion.status) ? (
            <Button
              className="text-warning"
              size="sm"
              variant="secondary"
              onPress={() => onPause(conversion)}
            >
              <PlayerPause aria-hidden="true" size={16} />
              {t("naming.pause")}
            </Button>
          ) : null}
          {conversion.status === "paused" ? (
            <Button
              className="text-success"
              size="sm"
              variant="secondary"
              onPress={() => onResume(conversion)}
            >
              <PlayerPlay aria-hidden="true" size={16} />
              {t("naming.resume")}
            </Button>
          ) : null}
          <Button
            isDisabled={conversion.status === "rolling_back"}
            size="sm"
            variant="danger-soft"
            onPress={() => onCancel(conversion)}
          >
            <PlayerStop aria-hidden="true" size={16} />
            {t("common.cancel")}
          </Button>
        </>
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

function sourceParseErrorText(
  error: unknown,
  t: ReturnType<typeof useTranslation>["t"],
): string {
  return sourceParseIssues(error, t)[0]?.message ?? errorText(error);
}

function sourceParseIssues(
  error: unknown,
  t: ReturnType<typeof useTranslation>["t"],
): LegacyConfigEditorIssue[] {
  if (!(error instanceof ApiError) || !isRecord(error.detail)) {
    return [{ message: errorText(error) }];
  }
  const issues = error.detail.issues;
  if (!Array.isArray(issues) || !issues.length || !isRecord(issues[0])) {
    return [{ message: t("naming.workflow.parseErrors.invalid") }];
  }
  const supportedCodes = new Set([
    "source_too_large",
    "source_empty",
    "no_legacy_naming_fields",
  ]);
  return issues.filter(isRecord).map((issue) => {
    const code = typeof issue.code === "string" ? issue.code : "invalid";
    const baseMessage = supportedCodes.has(code)
      ? t(`naming.workflow.parseErrors.${code}`)
      : t("naming.workflow.parseErrors.invalid");
    const line = typeof issue.line === "number" ? issue.line : null;
    return {
      line,
      column: typeof issue.column === "number" ? issue.column : null,
      message: line
        ? t("naming.workflow.errorAtLine", {
            line,
            message: baseMessage,
          })
        : baseMessage,
    };
  });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
