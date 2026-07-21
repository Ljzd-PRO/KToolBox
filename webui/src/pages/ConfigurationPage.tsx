import { Alert, Button, Chip, Surface, Tabs, toast } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Braces,
  Check,
  Cloud,
  Download,
  Eraser,
  FileCheck2,
  FileCog,
  FileText,
  Hash,
  KeyRound,
  ListTodo,
  PanelTop,
  Save,
  Search,
  Settings2,
  ShieldAlert,
  TextCursorInput,
  ToggleLeft,
  Undo2,
  X,
  type LucideIcon,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";

import {
  CodeEditor,
  ConfirmModal,
  FormField,
  FormSwitchField,
  FormSurface,
  NumberInput,
  PageHeader,
  PageLoading,
  PasswordField,
  SelectField,
} from "../components/ui";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { ConfigField, ConfigSchema, ProjectDocument, TextDocument } from "../types";

type DotenvName = "dotenv" | "production";
type RawName = DotenvName | "project";
type PendingValues = Record<string, string | null>;

const sourceColors: Record<string, "default" | "accent" | "warning" | "success"> = {
  default: "default",
  ".env": "accent",
  "prod.env": "success",
  environment: "warning",
};

export function ConfigurationPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const locale = i18n.language.startsWith("zh") ? "zh-CN" : "en";
  const schemaQuery = useQuery({
    queryKey: ["config-schema", locale],
    queryFn: () => api<ConfigSchema>(`/config/schema?locale=${locale}`),
  });
  const dotenvQuery = useQuery({
    queryKey: ["config-document", "dotenv"],
    queryFn: () => api<TextDocument>("/config/dotenv/dotenv"),
  });
  const productionQuery = useQuery({
    queryKey: ["config-document", "production"],
    queryFn: () => api<TextDocument>("/config/dotenv/production"),
  });
  const projectQuery = useQuery({
    queryKey: ["config-document", "project"],
    queryFn: () => api<ProjectDocument>("/config/project"),
  });
  const [destination, setDestination] = useState<DotenvName>("dotenv");
  const [section, setSection] = useState("api");
  const [filter, setFilter] = useState("");
  const [pending, setPending] = useState<Record<DotenvName, PendingValues>>({ dotenv: {}, production: {} });
  const [reviewing, setReviewing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [rawName, setRawName] = useState<RawName>("dotenv");
  const [rawDrafts, setRawDrafts] = useState<Partial<Record<RawName, string>>>({});

  const documents = useMemo(
    () => ({ dotenv: dotenvQuery.data, production: productionQuery.data, project: projectQuery.data }),
    [dotenvQuery.data, productionQuery.data, projectQuery.data],
  );

  if (schemaQuery.isLoading || dotenvQuery.isLoading || productionQuery.isLoading || projectQuery.isLoading) {
    return <PageLoading />;
  }

  const schema = schemaQuery.data;
  if (!schema) return null;
  const changed = pending[destination];
  const changedFields = schema.fields.filter((field) => field.env_name in changed);
  const sectionOptions = [
    { value: "all", label: t("configuration.allSections") },
    ...Object.entries(schema.sections).map(([value, label]) => ({ value, label })),
  ];
  const normalizedFilter = filter.trim().toLocaleLowerCase();
  const visibleFields = schema.fields.filter(
    (field) =>
      (section === "all" || field.section === section) &&
      (!normalizedFilter ||
        `${field.label} ${field.description} ${field.env_name}`.toLocaleLowerCase().includes(normalizedFilter)),
  );

  function updateField(field: ConfigField, value: string | null) {
    setPending((current) => ({
      ...current,
      [destination]: { ...current[destination], [field.env_name]: value },
    }));
  }

  function discardField(field: ConfigField) {
    setPending((current) => {
      const values = { ...current[destination] };
      delete values[field.env_name];
      return { ...current, [destination]: values };
    });
  }

  async function saveStructured() {
    if (!session || !documents[destination]) return;
    setSaving(true);
    try {
      await api<TextDocument>(`/config/dotenv/${destination}`, {
        method: "PATCH",
        body: { values: changed },
        csrfToken: session.csrf_token,
        headers: { "If-Match": documents[destination]?.revision ?? "" },
      });
      setPending((current) => ({ ...current, [destination]: {} }));
      setReviewing(false);
      await refreshConfiguration();
      toast.success(t("configuration.saved"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSaving(false);
    }
  }

  async function refreshConfiguration() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["config-schema"] }),
      queryClient.invalidateQueries({ queryKey: ["config-document"] }),
      queryClient.invalidateQueries({ queryKey: ["summary"] }),
    ]);
  }

  async function validateRaw() {
    const content = rawDrafts[rawName] ?? documents[rawName]?.content ?? "";
    const path = rawName === "project" ? "/config/project/validate" : `/config/dotenv/${rawName}/validate`;
    try {
      await api<{ valid: true }>(path, { method: "POST", body: { content } });
      toast.success(t("configuration.valid"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  async function saveRaw() {
    if (!session || !documents[rawName]) return;
    setSaving(true);
    const path = rawName === "project" ? "/config/project" : `/config/dotenv/${rawName}`;
    try {
      const document = await api<TextDocument | ProjectDocument>(path, {
        method: "PUT",
        body: { content: rawDrafts[rawName] ?? documents[rawName]?.content ?? "" },
        csrfToken: session.csrf_token,
        headers: { "If-Match": documents[rawName]?.revision ?? "" },
      });
      setRawDrafts((current) => ({ ...current, [rawName]: document.content }));
      await refreshConfiguration();
      toast.success(t("configuration.saved"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSaving(false);
    }
  }

  async function downloadExample() {
    try {
      const response = await fetch("/api/v1/config/example", { credentials: "same-origin" });
      if (!response.ok) throw new Error(response.statusText);
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "example.env";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-6">
      <PageHeader
        description={t("configuration.description")}
        title={t("configuration.title")}
        actions={
          <Button variant="outline" onPress={() => void downloadExample()}>
            <Download aria-hidden="true" size={17} />
            {t("configuration.example")}
          </Button>
        }
      />

      <Tabs className="min-w-0 w-full" aria-label={t("configuration.title")} defaultSelectedKey="structured" variant="secondary">
        <Tabs.ListContainer className="max-w-full overflow-x-auto">
          <Tabs.List>
            <Tabs.Tab id="structured">{t("configuration.structured")}<Tabs.Indicator /></Tabs.Tab>
            <Tabs.Tab id="effective">{t("configuration.effective")}<Tabs.Indicator /></Tabs.Tab>
            <Tabs.Tab id="advanced">{t("configuration.advanced")}<Tabs.Indicator /></Tabs.Tab>
          </Tabs.List>
        </Tabs.ListContainer>

        <Tabs.Panel className="min-w-0 pt-5" id="structured">
          <div className="grid gap-5">
            <FormSurface className="grid gap-4 lg:grid-cols-[minmax(0,220px)_minmax(0,260px)_1fr]">
              <SelectField
                icon={FileText}
                label={t("configuration.destination")}
                options={[
                  { value: "dotenv", label: t("configuration.environment") },
                  { value: "production", label: t("configuration.production") },
                ]}
                value={destination}
                onChange={(value) => setDestination(value as DotenvName)}
              />
              <SelectField icon={Settings2} label={t("configuration.section")} options={sectionOptions} value={section} onChange={setSection} />
              <FormField
                icon={Search}
                label={t("configuration.search")}
                placeholder={t("configuration.searchPlaceholder")}
                value={filter}
                onChange={setFilter}
              />
            </FormSurface>

            <FormSurface className="divide-y divide-border p-0">
              {visibleFields.map((field) => (
                <ConfigFieldEditor
                  field={field}
                  key={field.path}
                  pendingValue={changed[field.env_name]}
                  isPending={field.env_name in changed}
                  onChange={(value) => updateField(field, value)}
                  onDiscard={() => discardField(field)}
                />
              ))}
              <div className="config-save-bar sticky bottom-0 z-10 flex flex-wrap items-center justify-between gap-3 p-3">
                <Chip color={changedFields.length ? "accent" : "default"} variant="soft">
                  {t("configuration.pendingCount", { count: changedFields.length })}
                </Chip>
                <Button isDisabled={!changedFields.length} variant="primary" onPress={() => setReviewing(true)}>
                  <Save aria-hidden="true" size={17} />
                  {t("configuration.review")}
                </Button>
              </div>
            </FormSurface>
          </div>
        </Tabs.Panel>

        <Tabs.Panel className="min-w-0 pt-5" id="effective">
          <Surface className="divide-y divide-border rounded-lg border border-border">
            {schema.fields.map((field) => (
              <div className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_minmax(180px,0.7fr)_auto] md:items-center" key={field.path}>
                <div className="min-w-0">
                  <p className="font-medium text-foreground">{field.label}</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted">{field.description}</p>
                </div>
                <code className="min-w-0 break-all text-xs text-muted">{displayValue(field)}</code>
                <Chip color={sourceColors[field.source] ?? "default"} size="sm" variant="soft">
                  {configurationSourceLabel(field.source, t)}
                </Chip>
              </div>
            ))}
          </Surface>
        </Tabs.Panel>

        <Tabs.Panel className="min-w-0 pt-5" id="advanced">
          <div className="grid gap-4">
            <Alert status="warning">
              <Alert.Indicator><ShieldAlert aria-hidden="true" size={19} /></Alert.Indicator>
              <Alert.Content>
                <Alert.Title>{t("configuration.advanced")}</Alert.Title>
                <Alert.Description>{t("configuration.rawWarning")}</Alert.Description>
              </Alert.Content>
            </Alert>
            <FormSurface className="grid gap-4">
              <SelectField
                icon={FileCog}
                label={t("configuration.file")}
                options={[
                  { value: "dotenv", label: t("configuration.environment") },
                  { value: "production", label: t("configuration.production") },
                  { value: "project", label: t("configuration.projectToml") },
                ]}
                value={rawName}
                onChange={(value) => setRawName(value as RawName)}
              />
              <CodeEditor
                description={`${t("configuration.filePath")}: ${documents[rawName]?.path ?? ""}`}
                icon={Braces}
                label={rawName === "project" ? "ktoolbox.toml" : rawName === "dotenv" ? ".env" : "prod.env"}
                rows={22}
                value={rawDrafts[rawName] ?? documents[rawName]?.content ?? ""}
                onChange={(content) => setRawDrafts((current) => ({ ...current, [rawName]: content }))}
              />
              <div className="flex flex-wrap justify-end gap-2">
                <Button variant="outline" onPress={() => void validateRaw()}>
                  <FileCheck2 aria-hidden="true" size={17} />
                  {t("configuration.validate")}
                </Button>
                <Button isPending={saving} variant="primary" onPress={() => void saveRaw()}>
                  <Save aria-hidden="true" size={17} />
                  {t("common.save")}
                </Button>
              </div>
            </FormSurface>
          </div>
        </Tabs.Panel>
      </Tabs>

      <ConfirmModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setReviewing(false)}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
            <Button isPending={saving} variant="primary" onPress={() => void saveStructured()}><Check aria-hidden="true" size={17} />{t("common.save")}</Button>
          </>
        }
        open={reviewing}
        title={t("configuration.reviewTitle")}
        onOpenChange={setReviewing}
      >
        <div className="divide-y divide-border">
          {changedFields.map((field) => (
            <div className="grid gap-2 py-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]" key={field.path}>
              <div>
                <p className="text-sm font-medium">{field.label}</p>
                <code className="text-xs text-muted">{field.env_name}</code>
              </div>
              <div className="text-sm sm:text-right">
                <span className="text-muted">{displayValue(field)}</span>
                <span aria-hidden="true"> → </span>
                <strong className="break-all">{field.secret ? "••••••••" : changed[field.env_name] ?? t("configuration.clear")}</strong>
              </div>
            </div>
          ))}
        </div>
      </ConfirmModal>
    </div>
  );
}

function ConfigFieldEditor({
  field,
  pendingValue,
  isPending,
  onChange,
  onDiscard,
}: {
  field: ConfigField;
  pendingValue: string | null | undefined;
  isPending: boolean;
  onChange: (value: string | null) => void;
  onDiscard: () => void;
}) {
  const { t } = useTranslation();
  const disabled = field.source === "environment";
  const schema = field.json_schema;
  const type = schemaType(schema);
  const value = isPending ? pendingValue : serializeValue(field.value ?? field.default);
  const enumValues = schemaEnum(schema);
  const icon = configurationIcon(field, type);
  const control = field.secret ? (
    <PasswordField
      description={field.description}
      icon={icon}
      isDisabled={disabled}
      label={field.label}
      placeholder={field.is_set ? "••••••••" : ""}
      value={isPending ? pendingValue ?? "" : ""}
      onChange={onChange}
    />
  ) : type === "boolean" ? (
    <FormSwitchField
      description={field.description}
      icon={icon}
      isDisabled={disabled}
      isSelected={String(value).toLocaleLowerCase() === "true"}
      label={field.label}
      onChange={(selected) => onChange(String(selected))}
    />
  ) : type === "integer" || type === "number" ? (
    <NumberInput
      description={field.description}
      icon={icon}
      isDisabled={disabled}
      label={field.label}
      maxValue={schemaNumber(schema, "maximum")}
      minValue={schemaNumber(schema, "minimum")}
      step={type === "integer" ? 1 : undefined}
      value={value === "" ? undefined : Number(value)}
      onChange={(next) => onChange(String(next))}
    />
  ) : enumValues.length ? (
    <SelectField
      description={field.description}
      icon={icon}
      isDisabled={disabled}
      label={field.label}
      options={enumValues.map((item) => ({ value: String(item), label: String(item) }))}
      value={value ?? ""}
      onChange={onChange}
    />
  ) : (
    <FormField
      description={field.description}
      icon={icon}
      label={field.label}
      value={value ?? ""}
      onChange={onChange}
    />
  );

  return (
    <div className="grid gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
      <div className="min-w-0">{control}</div>
      <div className="flex flex-wrap items-center gap-2 lg:max-w-60 lg:justify-end">
        <Chip color={sourceColors[field.source] ?? "default"} size="sm" variant="soft">
          {configurationSourceLabel(field.source, t)}
        </Chip>
        <Chip color={field.apply_mode === "restart" ? "warning" : "success"} size="sm" variant="soft">
          {field.apply_mode === "restart" ? t("configuration.restart") : t("configuration.nextTask")}
        </Chip>
        {disabled ? <Chip color="warning" size="sm" variant="soft">{t("configuration.inherited")}</Chip> : null}
        {isPending ? <Button size="sm" variant="ghost" onPress={onDiscard}><Undo2 aria-hidden="true" size={15} />{t("common.undo")}</Button> : null}
        {!disabled && field.source !== "default" ? (
          <Button size="sm" variant="ghost" onPress={() => onChange(null)}><Eraser aria-hidden="true" size={15} />{t("configuration.clear")}</Button>
        ) : null}
      </div>
    </div>
  );
}

function configurationIcon(field: ConfigField, type: string | undefined): LucideIcon {
  if (field.secret) return KeyRound;
  if (type === "boolean") return ToggleLeft;
  if (type === "integer" || type === "number") return Hash;
  const section = field.path.split(".", 1)[0];
  if (section === "api") return Cloud;
  if (section === "downloader") return Download;
  if (section === "job") return ListTodo;
  if (section === "webui") return PanelTop;
  return TextCursorInput;
}

function configurationSourceLabel(source: string, t: TFunction): string {
  if (source === "default") return t("configuration.sourceDefault");
  if (source === "environment") return t("configuration.sourceEnvironment");
  return source;
}

function schemaType(schema: Record<string, unknown>): string | undefined {
  if (typeof schema.type === "string") return schema.type;
  const branches = Array.isArray(schema.anyOf) ? schema.anyOf : [];
  return branches.map((branch) => schemaType(branch as Record<string, unknown>)).find((type) => type && type !== "null");
}

function schemaEnum(schema: Record<string, unknown>): unknown[] {
  if (Array.isArray(schema.enum)) return schema.enum;
  const branches = Array.isArray(schema.anyOf) ? schema.anyOf : [];
  return branches.flatMap((branch) => schemaEnum(branch as Record<string, unknown>));
}

function schemaNumber(schema: Record<string, unknown>, key: "minimum" | "maximum"): number | undefined {
  if (typeof schema[key] === "number") return schema[key];
  const branches = Array.isArray(schema.anyOf) ? schema.anyOf : [];
  return branches.map((branch) => schemaNumber(branch as Record<string, unknown>, key)).find((value) => value !== undefined);
}

function serializeValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function displayValue(field: ConfigField): string {
  if (field.secret) return field.is_set ? "••••••••" : "—";
  return serializeValue(field.value) || "—";
}
