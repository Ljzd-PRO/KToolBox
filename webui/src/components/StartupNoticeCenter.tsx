import { Alert, Button, Chip, Surface, toast } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconAlertTriangle as AlertTriangle,
  IconArrowLeft as ArrowLeft,
  IconArrowRight as ArrowRight,
  IconCheck as Check,
  IconDatabaseImport as DatabaseImport,
  IconFolder as Folder,
  IconFolderPlus as FolderPlus,
  IconListCheck as ListCheck,
  IconRefresh as Refresh,
  IconTerminal2 as Terminal,
  IconX as X,
} from "@tabler/icons-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatBytes } from "../lib/format";
import { TASK_OUTPUT_PATH_SELECTOR } from "../lib/pathSelectors";
import type {
  LegacyNamingMigration,
  LegacyNamingMigrationResult,
  NamingLegacyContext,
  NamingPreview,
} from "../types";
import { RemotePathField } from "./RemotePathField";
import {
  FormCheckbox,
  FormModal,
  FormSurface,
  InlineCode,
} from "./ui";

type MigrationPhase = "fields" | "review" | "directories" | "preview";

function displayValue(value: unknown): string {
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

const LEGACY_FIELD_LABELS: Record<string, string> = {
  post_dirname_format: "workTemplate",
  "post_structure.attachments": "attachmentsDirectory",
  "post_structure.content": "contentFile",
  "post_structure.external_links": "externalLinksFile",
  "post_structure.file": "primaryFileTemplate",
  "post_structure.revisions": "revisionsDirectory",
  mix_posts: "mixWorks",
  sequential_filename: "sequentialFiles",
  sequential_filename_excludes: "sequentialExclusions",
  filename_format: "attachmentFileTemplate",
  group_by_year: "groupByYear",
  group_by_month: "groupByMonth",
  year_dirname_format: "yearTemplate",
  month_dirname_format: "monthTemplate",
};

function fieldLabel(path: string, t: (key: string) => string): string {
  const key = LEGACY_FIELD_LABELS[path];
  return key ? t(`naming.${key}`) : path;
}

export function StartupNoticeCenter() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const migrationQuery = useQuery({
    queryKey: ["legacy-naming-migration"],
    queryFn: () => api<LegacyNamingMigration>("/naming/legacy-migration"),
  });
  const legacyContextQuery = useQuery({
    queryKey: ["naming-legacy-context"],
    queryFn: () => api<NamingLegacyContext>("/naming/legacy-context"),
  });
  const migration = migrationQuery.data;
  const [phase, setPhase] = useState<MigrationPhase>("fields");
  const [dismissedRevision, setDismissedRevision] = useState<string | null>(null);
  const [fieldSelection, setFieldSelection] = useState<{
    revision: string;
    values: Set<string>;
  } | null>(null);
  const [rootSelection, setRootSelection] = useState<string[] | null>(null);
  const [preview, setPreview] = useState<NamingPreview | null>(null);
  const [selectedCreators, setSelectedCreators] = useState<Set<string>>(new Set());
  const [working, setWorking] = useState(false);
  const pending = Boolean(
    migration?.pending &&
    migration.project_revision !== dismissedRevision,
  );
  const open = pending || phase === "directories" || phase === "preview";
  const selectedFields = useMemo(
    () => (
      migration && fieldSelection?.revision === migration.project_revision
        ? fieldSelection.values
        : new Set(migration?.fields.map((field) => field.path) ?? [])
    ),
    [fieldSelection, migration],
  );
  const roots = rootSelection ?? legacyContextQuery.data?.roots ?? [];

  const sourceRevisions = useMemo(
    () => Object.fromEntries(
      (migration?.sources ?? []).map((source) => [source.name, source.revision]),
    ),
    [migration?.sources],
  );

  function setSelectedFields(values: Set<string>) {
    if (!migration) return;
    setFieldSelection({ revision: migration.project_revision, values });
  }

  function setRoots(values: string[]) {
    setRootSelection(values);
  }

  function closeForNow() {
    if (migration?.pending) setDismissedRevision(migration.project_revision);
    setPhase("fields");
    setPreview(null);
  }

  async function applyConfigurationMigration() {
    if (!migration || !session) return;
    setWorking(true);
    try {
      const result = await api<LegacyNamingMigrationResult>(
        "/naming/legacy-migration/apply",
        {
          method: "POST",
          body: {
            selected_fields: [...selectedFields],
            project_revision: migration.project_revision,
            source_revisions: sourceRevisions,
          },
          csrfToken: session.csrf_token,
        },
      );
      queryClient.setQueryData<LegacyNamingMigration>(
        ["legacy-naming-migration"],
        (current) => current
          ? { ...current, pending: false, fields: [], project_revision: result.project_revision }
          : current,
      );
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["naming"] }),
        queryClient.invalidateQueries({ queryKey: ["naming-legacy-context"] }),
        queryClient.invalidateQueries({ queryKey: ["project"] }),
      ]);
      setRoots(legacyContextQuery.data?.roots ?? []);
      setPhase("directories");
    } catch (error) {
      toast.danger(t("naming.migration.failed"), {
        description: errorText(error),
      });
    } finally {
      setWorking(false);
    }
  }

  async function scanDirectories() {
    if (!session || roots.some((root) => !root.trim()) || !roots.length) return;
    setWorking(true);
    try {
      const result = await api<NamingPreview>("/naming/preview", {
        method: "POST",
        body: { roots },
        csrfToken: session.csrf_token,
      });
      setPreview(result);
      setSelectedCreators(
        new Set(
          result.creators
            .filter((creator) => creator.selectable)
            .map((creator) => creator.key),
        ),
      );
      setPhase("preview");
    } catch (error) {
      toast.danger(t("naming.previewFailed"), {
        description: errorText(error),
      });
    } finally {
      setWorking(false);
    }
  }

  async function applyDirectoryConversion() {
    if (!session || !preview) return;
    setWorking(true);
    try {
      await api("/naming/apply", {
        method: "POST",
        body: {
          preview_id: preview.id,
          selected_creators: [...selectedCreators],
        },
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["naming-conversions"] });
      setPhase("fields");
      setPreview(null);
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setWorking(false);
    }
  }

  if (!migration) return null;

  return (
    <FormModal
      isWide
      open={open}
      size="lg"
      title={t("naming.migration.title")}
      actions={
        <MigrationActions
          phase={phase}
          working={working}
          canScan={roots.length > 0 && roots.every((root) => Boolean(root.trim()))}
          canConvert={Boolean(
            preview &&
            preview.conflict_count === 0 &&
            (
              preview.creators.every((creator) => !creator.selectable) ||
              selectedCreators.size > 0
            ),
          )}
          onBack={() => setPhase(phase === "review" ? "fields" : "directories")}
          onClose={closeForNow}
          onContinue={() => setPhase("review")}
          onMigrate={() => void applyConfigurationMigration()}
          onScan={() => void scanDirectories()}
          onConvert={() => void applyDirectoryConversion()}
        />
      }
      onOpenChange={(nextOpen) => {
        if (!nextOpen) closeForNow();
      }}
    >
      <div className="grid gap-5">
        <MigrationSteps phase={phase} />
        {phase === "fields" ? (
          <FieldSelection
            migration={migration}
            selected={selectedFields}
            onChange={setSelectedFields}
          />
        ) : null}
        {phase === "review" ? (
          <MigrationReview migration={migration} selected={selectedFields} />
        ) : null}
        {phase === "directories" ? (
          <DirectorySelection roots={roots} onChange={setRoots} />
        ) : null}
        {phase === "preview" && preview ? (
          <DirectoryPreview
            preview={preview}
            selected={selectedCreators}
            onChange={setSelectedCreators}
          />
        ) : null}
      </div>
    </FormModal>
  );
}

function MigrationSteps({ phase }: { phase: MigrationPhase }) {
  const { t } = useTranslation();
  const current = { fields: 1, review: 2, directories: 3, preview: 4 }[phase];
  return (
    <ol className="grid grid-cols-2 gap-2 sm:grid-cols-4" aria-label={t("naming.migration.progress")}>
      {[
        t("naming.migration.configStep"),
        t("naming.migration.reviewStep"),
        t("naming.migration.directoryStep"),
        t("naming.migration.previewStep"),
      ].map((label, index) => {
        const step = index + 1;
        return (
          <li
            className={`flex min-h-11 items-center gap-2 rounded-lg border px-3 text-sm font-semibold ${
              step === current
                ? "border-accent bg-accent-soft text-accent-soft-foreground"
                : step < current
                  ? "border-success/40 bg-success/10 text-success"
                  : "border-border bg-default text-muted"
            }`}
            key={label}
          >
            <span className="grid size-6 shrink-0 place-items-center rounded-full border border-current text-xs">
              {step < current ? <Check aria-hidden="true" size={13} /> : step}
            </span>
            <span className="min-w-0 truncate">{label}</span>
          </li>
        );
      })}
    </ol>
  );
}

function FieldSelection({
  migration,
  selected,
  onChange,
}: {
  migration: LegacyNamingMigration;
  selected: Set<string>;
  onChange: (selected: Set<string>) => void;
}) {
  const { t } = useTranslation();

  function toggle(path: string, isSelected: boolean) {
    const next = new Set(selected);
    if (isSelected) next.add(path);
    else next.delete(path);
    onChange(next);
  }

  return (
    <>
      <Alert status="warning">
        <Alert.Indicator>
          <AlertTriangle aria-hidden="true" size={18} />
        </Alert.Indicator>
        <Alert.Content>
          <Alert.Title>{t("naming.migration.detected")}</Alert.Title>
          <Alert.Description>{t("naming.migration.detectedBody")}</Alert.Description>
        </Alert.Content>
      </Alert>
      <FormSurface className="grid gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-foreground">{t("naming.migration.fieldsTitle")}</h3>
            <p className="mt-1 text-sm text-muted">{t("naming.migration.fieldsBody")}</p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" onPress={() => onChange(new Set())}>
              {t("naming.migration.clearSelection")}
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onPress={() => onChange(new Set(migration.fields.map((field) => field.path)))}
            >
              <ListCheck aria-hidden="true" size={16} />
              {t("naming.migration.selectAll")}
            </Button>
          </div>
        </div>
        <div className="grid gap-2">
          {migration.fields.map((field) => (
            <FormCheckbox
              description={t("naming.migration.useLegacyValue")}
              isSelected={selected.has(field.path)}
              key={field.path}
              label={
                <span className="flex min-w-0 flex-wrap items-center gap-2">
                  <span>{fieldLabel(field.path, t)}</span>
                  {field.sources.map((source) => (
                    <Chip key={source} size="sm" variant="soft">{source}</Chip>
                  ))}
                </span>
              }
              onChange={(isSelected) => toggle(field.path, isSelected)}
            />
          ))}
        </div>
      </FormSurface>
      {migration.ignored_environment_keys.length ? (
        <Alert status="warning">
          <Alert.Indicator><Terminal aria-hidden="true" size={18} /></Alert.Indicator>
          <Alert.Content>
            <Alert.Title>{t("naming.migration.environmentTitle")}</Alert.Title>
            <Alert.Description>
              {t("naming.migration.environmentBody")}
              <span className="mt-2 flex flex-wrap gap-1.5">
                {migration.ignored_environment_keys.map((key) => (
                  <InlineCode key={key}>{key}</InlineCode>
                ))}
              </span>
            </Alert.Description>
          </Alert.Content>
        </Alert>
      ) : null}
    </>
  );
}

function MigrationReview({
  migration,
  selected,
}: {
  migration: LegacyNamingMigration;
  selected: Set<string>;
}) {
  const { t } = useTranslation();
  return (
    <div className="grid gap-4">
      <div>
        <h3 className="text-lg font-semibold text-foreground">{t("naming.migration.reviewTitle")}</h3>
        <p className="mt-1 text-sm leading-6 text-muted">{t("naming.migration.reviewBody")}</p>
      </div>
      <div className="grid gap-3">
        {migration.fields.map((field) => {
          const useLegacy = selected.has(field.path);
          return (
            <Surface className="grid gap-3 rounded-lg border border-border p-3 shadow-none" key={field.path}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold text-foreground">{fieldLabel(field.path, t)}</span>
                <Chip color={useLegacy ? "accent" : "default"} size="sm" variant="soft">
                  {t(useLegacy ? "naming.migration.useOld" : "naming.migration.keepCurrent")}
                </Chip>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <ValueComparison
                  active={useLegacy}
                  label={t("naming.migration.oldValue")}
                  value={field.legacy_value}
                />
                <ValueComparison
                  active={!useLegacy}
                  label={t("naming.migration.currentValue")}
                  value={field.current_value}
                />
              </div>
            </Surface>
          );
        })}
      </div>
    </div>
  );
}

function ValueComparison({
  active,
  label,
  value,
}: {
  active: boolean;
  label: string;
  value: unknown;
}) {
  return (
    <div className={`grid gap-1 rounded-lg border p-3 ${active ? "border-accent bg-accent-soft" : "border-border bg-default"}`}>
      <span className="text-xs font-semibold text-muted">{label}</span>
      <InlineCode className="break-all">{displayValue(value)}</InlineCode>
    </div>
  );
}

function DirectorySelection({
  roots,
  onChange,
}: {
  roots: string[];
  onChange: (roots: string[]) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="grid gap-4">
      <Alert status="success">
        <Alert.Indicator><Check aria-hidden="true" size={18} /></Alert.Indicator>
        <Alert.Content>
          <Alert.Title>{t("naming.migration.success")}</Alert.Title>
          <Alert.Description>{t("naming.migration.directoryBody")}</Alert.Description>
        </Alert.Content>
      </Alert>
      <FormSurface className="grid gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-foreground">{t("naming.legacyRoots")}</h3>
            <p className="mt-1 text-sm text-muted">{t("naming.legacyRootsHint")}</p>
          </div>
          <Button
            size="sm"
            variant="secondary"
            onPress={() => onChange([...roots, ""])}
          >
            <FolderPlus aria-hidden="true" size={16} />
            {t("naming.addLegacyRoot")}
          </Button>
        </div>
        {roots.map((root, index) => (
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-2" key={index}>
            <RemotePathField
              icon={Folder}
              label={t("naming.legacyRootNumber", { number: index + 1 })}
              selector={TASK_OUTPUT_PATH_SELECTOR}
              value={root}
              onChange={(value) => onChange(roots.map((item, itemIndex) => itemIndex === index ? value : item))}
            />
            <Button
              isIconOnly
              aria-label={t("naming.removeLegacyRoot", { number: index + 1 })}
              className="mb-0.5"
              variant="ghost"
              onPress={() => onChange(roots.filter((_, itemIndex) => itemIndex !== index))}
            >
              <X aria-hidden="true" size={17} />
            </Button>
          </div>
        ))}
      </FormSurface>
    </div>
  );
}

function DirectoryPreview({
  preview,
  selected,
  onChange,
}: {
  preview: NamingPreview;
  selected: Set<string>;
  onChange: (selected: Set<string>) => void;
}) {
  const { t } = useTranslation();

  function toggle(key: string, isSelected: boolean) {
    const next = new Set(selected);
    if (isSelected) next.add(key);
    else next.delete(key);
    onChange(next);
  }

  return (
    <div className="grid gap-4">
      <div>
        <h3 className="text-lg font-semibold text-foreground">{t("naming.migration.previewTitle")}</h3>
        <p className="mt-1 text-sm leading-6 text-muted">{t("naming.reviewDescription")}</p>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          [t("naming.stats.creators"), preview.creator_count],
          [t("naming.stats.works"), preview.work_count],
          [t("naming.stats.files"), preview.file_count],
          [t("naming.stats.size"), formatBytes(preview.total_bytes)],
        ].map(([label, value]) => (
          <Surface className="rounded-lg border border-border p-3 text-center shadow-none" key={String(label)}>
            <div className="text-lg font-bold text-foreground">{value}</div>
            <div className="mt-1 text-xs font-semibold text-muted">{label}</div>
          </Surface>
        ))}
      </div>
      {preview.conflict_count ? (
        <Alert status="danger">
          <Alert.Indicator><AlertTriangle aria-hidden="true" size={18} /></Alert.Indicator>
          <Alert.Content>
            <Alert.Title>{t("naming.conflictCount", { count: preview.conflict_count })}</Alert.Title>
            <Alert.Description>{t("naming.conflictBody")}</Alert.Description>
          </Alert.Content>
        </Alert>
      ) : null}
      <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
        {preview.creators.map((creator) => (
          <FormCheckbox
            description={`${creator.works} / ${creator.files} / ${formatBytes(creator.bytes)}`}
            isDisabled={!creator.selectable}
            isSelected={selected.has(creator.key)}
            key={creator.key}
            label={
              <span className="grid min-w-0">
                <span className="truncate">{creator.name}</span>
                <InlineCode className="mt-1 block truncate">{creator.source}</InlineCode>
              </span>
            }
            onChange={(isSelected) => toggle(creator.key, isSelected)}
          />
        ))}
      </div>
    </div>
  );
}

function MigrationActions({
  phase,
  working,
  canScan,
  canConvert,
  onBack,
  onClose,
  onContinue,
  onMigrate,
  onScan,
  onConvert,
}: {
  phase: MigrationPhase;
  working: boolean;
  canScan: boolean;
  canConvert: boolean;
  onBack: () => void;
  onClose: () => void;
  onContinue: () => void;
  onMigrate: () => void;
  onScan: () => void;
  onConvert: () => void;
}) {
  const { t } = useTranslation();
  return (
    <>
      {phase !== "fields" ? (
        <Button isDisabled={working} variant="ghost" onPress={onBack}>
          <ArrowLeft aria-hidden="true" size={17} />
          {t("common.back")}
        </Button>
      ) : null}
      <Button isDisabled={working} variant="ghost" onPress={onClose}>
        <X aria-hidden="true" size={17} />
        {t(phase === "directories" ? "naming.migration.later" : "naming.startup.ignore")}
      </Button>
      {phase === "fields" ? (
        <Button variant="primary" onPress={onContinue}>
          <ArrowRight aria-hidden="true" size={17} />
          {t("naming.migration.continue")}
        </Button>
      ) : null}
      {phase === "review" ? (
        <Button isPending={working} variant="primary" onPress={onMigrate}>
          <DatabaseImport aria-hidden="true" size={17} />
          {t("naming.migration.migrate")}
        </Button>
      ) : null}
      {phase === "directories" ? (
        <Button isDisabled={!canScan} isPending={working} variant="primary" onPress={onScan}>
          <Refresh aria-hidden="true" size={17} />
          {t("naming.migration.scanNow")}
        </Button>
      ) : null}
      {phase === "preview" ? (
        <Button isDisabled={!canConvert} isPending={working} variant="primary" onPress={onConvert}>
          <Check aria-hidden="true" size={17} />
          {t("naming.migration.applyConversion")}
        </Button>
      ) : null}
    </>
  );
}
