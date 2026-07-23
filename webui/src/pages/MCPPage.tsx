import {
  Accordion,
  Button,
  Chip,
  SearchField,
  Surface,
  Table,
  Tabs,
  toast,
} from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconAlertTriangle,
  IconCheck,
  IconClock,
  IconCode,
  IconCopy,
  IconDownload,
  IconKey,
  IconPlugConnected,
  IconPlus,
  IconSearch,
  IconShieldLock,
  IconTrash,
  IconWorld,
  IconX,
} from "@tabler/icons-react";
import { useMemo, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import {
  ConfirmModal,
  DataTableFrame,
  EmptyPanel,
  FormField,
  FormModal,
  FormSurface,
  PageHeader,
  PageLoading,
  PasswordField,
  SelectField,
} from "../components/ui";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  mcpClientConfiguration,
  mcpClientKeys,
  mcpReadyConfiguration,
  type MCPClientKey,
} from "../lib/mcp";
import { formatDateTime } from "../lib/format";
import type {
  MCPStatus,
  MCPToken,
  MCPTokenCreateRequest,
  MCPTokenCreated,
  MCPTool,
} from "../types";

type ToolScopeFilter = "all" | "mcp:read" | "mcp:write";
type TokenStatus = "active" | "expired" | "revoked";

const permissionOptions = [
  { value: "read", icon: IconShieldLock, tone: "accent" as const },
  { value: "manage", icon: IconKey, tone: "warning" as const },
];

const expiryValues = ["7", "30", "90", "365", "never"] as const;

function tokenStatus(token: MCPToken): TokenStatus {
  if (token.revoked_at) return "revoked";
  if (!token.active) return "expired";
  return "active";
}

function statusColor(status: TokenStatus): "success" | "warning" | "danger" {
  if (status === "active") return "success";
  if (status === "expired") return "warning";
  return "danger";
}

function safetyColor(safety: MCPTool["safety"]): "success" | "warning" | "danger" {
  if (safety === "read") return "success";
  if (safety === "write") return "warning";
  return "danger";
}

function EndpointRow({
  label,
  value,
  copyLabel,
  onCopy,
}: {
  label: string;
  value: string;
  copyLabel: string;
  onCopy: () => void;
}) {
  return (
    <div className="grid min-w-0 gap-2 border-b border-border py-3 last:border-b-0 sm:grid-cols-[9rem_minmax(0,1fr)_auto] sm:items-center">
      <span className="text-sm font-medium text-muted">{label}</span>
      <code className="min-w-0 break-all text-xs leading-relaxed text-foreground">{value}</code>
      <Button className="w-fit" size="sm" variant="ghost" onPress={onCopy}>
        <IconCopy aria-hidden="true" size={16} />
        {copyLabel}
      </Button>
    </div>
  );
}

function TokenStatusChips({ token }: { token: MCPToken }) {
  const { t } = useTranslation();
  const status = tokenStatus(token);
  return (
    <div className="flex flex-wrap gap-1.5">
      <Chip color={statusColor(status)} size="sm" variant="soft">
        {t(`mcp.tokenStatuses.${status}`)}
      </Chip>
      {!token.expires_at ? (
        <Chip color="warning" size="sm" variant="soft">
          <IconAlertTriangle aria-hidden="true" size={13} />
          {t("mcp.permanent")}
        </Chip>
      ) : null}
    </div>
  );
}

export function MCPPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: ["mcp", "status"], queryFn: () => api<MCPStatus>("/mcp/status") });
  const tokens = useQuery({ queryKey: ["mcp", "tokens"], queryFn: () => api<MCPToken[]>("/mcp/tokens") });
  const tools = useQuery({ queryKey: ["mcp", "tools"], queryFn: () => api<MCPTool[]>("/mcp/tools") });
  const [createOpen, setCreateOpen] = useState(false);
  const [createdToken, setCreatedToken] = useState<MCPTokenCreated | null>(null);
  const [revoking, setRevoking] = useState<MCPToken | null>(null);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [permission, setPermission] = useState<"read" | "manage">("read");
  const [expiry, setExpiry] = useState<(typeof expiryValues)[number]>("30");
  const [client, setClient] = useState<MCPClientKey>("general");
  const [toolSearch, setToolSearch] = useState("");
  const [scopeFilter, setScopeFilter] = useState<ToolScopeFilter>("all");

  const origin = window.location.origin;
  const endpoint = `${origin}${status.data?.endpoint_path ?? "/mcp"}`;
  const openapi = `${origin}${status.data?.openapi_path ?? "/api/v1/openapi.yaml"}`;

  const visibleTools = useMemo(() => {
    const query = toolSearch.trim().toLocaleLowerCase(i18n.resolvedLanguage);
    return (tools.data ?? []).filter((tool) => {
      if (scopeFilter !== "all" && tool.scope !== scopeFilter) return false;
      const description = t(`mcp.toolDescriptions.${tool.name}`, { defaultValue: tool.description });
      return !query || `${tool.name} ${description} ${tool.category}`.toLocaleLowerCase(i18n.resolvedLanguage).includes(query);
    });
  }, [i18n.resolvedLanguage, scopeFilter, t, toolSearch, tools.data]);

  const toolGroups = useMemo(() => {
    const groups = new Map<string, MCPTool[]>();
    for (const tool of visibleTools) {
      const group = groups.get(tool.category) ?? [];
      group.push(tool);
      groups.set(tool.category, group);
    }
    return [...groups.entries()].sort(([left], [right]) => left.localeCompare(right));
  }, [visibleTools]);
  const expandToolGroups = Boolean(toolSearch.trim()) || scopeFilter !== "all" || toolGroups.length === 1;

  if (status.isLoading || tokens.isLoading || tools.isLoading) return <PageLoading />;

  async function copy(value: string, label: string) {
    try {
      await navigator.clipboard.writeText(value);
      toast.success(t("mcp.copied"), { description: label });
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  function resetCreateForm() {
    setName("");
    setPassword("");
    setPermission("read");
    setExpiry("30");
  }

  async function createToken(event: FormEvent) {
    event.preventDefault();
    if (!session || !name.trim() || !password) return;
    setSaving(true);
    try {
      const payload: MCPTokenCreateRequest = {
        name: name.trim(),
        password,
        permission,
        expires_in_days: expiry === "never" ? null : Number(expiry) as 7 | 30 | 90 | 365,
      };
      const created = await api<MCPTokenCreated>("/mcp/tokens", {
        method: "POST",
        body: payload,
        csrfToken: session.csrf_token,
      });
      setCreateOpen(false);
      resetCreateForm();
      setCreatedToken(created);
      await queryClient.invalidateQueries({ queryKey: ["mcp", "tokens"] });
      toast.success(t("mcp.tokenCreated"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSaving(false);
    }
  }

  async function revokeToken() {
    if (!session || !revoking) return;
    setSaving(true);
    try {
      await api<MCPToken>(`/mcp/tokens/${encodeURIComponent(revoking.id)}/revoke`, {
        method: "POST",
        csrfToken: session.csrf_token,
      });
      setRevoking(null);
      await queryClient.invalidateQueries({ queryKey: ["mcp", "tokens"] });
      toast.success(t("mcp.tokenRevoked"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSaving(false);
    }
  }

  const permissionSelectOptions = permissionOptions.map((option) => ({
    ...option,
    label: t(`mcp.permissions.${option.value}`),
    description: t(`mcp.permissionHints.${option.value}`),
  }));
  const expiryOptions = expiryValues.map((value) => ({
    value,
    label: value === "never" ? t("mcp.expiryNever") : t("mcp.expiryDays", { count: Number(value) }),
    icon: value === "never" ? IconAlertTriangle : IconClock,
    tone: value === "never" ? "warning" as const : "default" as const,
  }));
  const scopeOptions = [
    { value: "all", label: t("mcp.allPermissions") },
    { value: "mcp:read", label: t("mcp.permissions.read"), icon: IconShieldLock, tone: "accent" as const },
    { value: "mcp:write", label: t("mcp.permissions.manage"), icon: IconKey, tone: "warning" as const },
  ];

  return (
    <div className="grid min-w-0 gap-6">
      <PageHeader
        showDescription
        description={t("mcp.description")}
        title={t("mcp.title")}
        actions={(
          <Button variant="primary" onPress={() => setCreateOpen(true)}>
            <IconPlus aria-hidden="true" size={18} />
            {t("mcp.newToken")}
          </Button>
        )}
      />

      <Surface className="flex min-w-0 items-start gap-3 rounded-lg border border-warning-soft-border bg-warning-soft p-4 text-warning-soft-foreground">
        <IconShieldLock aria-hidden="true" className="mt-0.5 shrink-0" size={20} />
        <div className="min-w-0">
          <h2 className="text-sm font-semibold">{t("mcp.securityTitle")}</h2>
          <p className="mt-1 text-sm leading-relaxed">{t("mcp.securityBody")}</p>
        </div>
      </Surface>

      <section aria-labelledby="mcp-service-heading" className="grid min-w-0 gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold" id="mcp-service-heading">{t("mcp.serviceStatus")}</h2>
          <Chip color={status.data?.running ? "success" : "danger"} variant="soft">
            <IconPlugConnected aria-hidden="true" size={15} />
            {status.data?.running ? t("mcp.running") : t("mcp.unavailable")}
          </Chip>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Surface className="rounded-lg border border-border p-4">
            <p className="text-sm text-muted">{t("mcp.transport")}</p>
            <p className="mt-2 font-semibold">{t("mcp.streamableHttp")}</p>
          </Surface>
          <Surface className="rounded-lg border border-border p-4">
            <p className="text-sm text-muted">{t("mcp.toolCount")}</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums">{status.data?.tool_count ?? 0}</p>
          </Surface>
          <Surface className="rounded-lg border border-border p-4 sm:col-span-2 lg:col-span-1">
            <p className="text-sm text-muted">{t("mcp.authentication")}</p>
            <p className="mt-2 font-semibold">{t("mcp.bearerToken")}</p>
          </Surface>
        </div>
        <FormSurface className="px-4 py-1">
          <EndpointRow
            copyLabel={t("mcp.copy")}
            label={t("mcp.mcpUrl")}
            value={endpoint}
            onCopy={() => void copy(endpoint, t("mcp.mcpUrl"))}
          />
          <EndpointRow
            copyLabel={t("mcp.copy")}
            label={t("mcp.openapiUrl")}
            value={openapi}
            onCopy={() => void copy(openapi, t("mcp.openapiUrl"))}
          />
          <div className="flex flex-wrap justify-end gap-2 py-3">
            <Button size="sm" variant="outline" onPress={() => window.open(openapi, "_blank", "noopener,noreferrer")}>
              <IconDownload aria-hidden="true" size={16} />
              {t("mcp.downloadOpenapi")}
            </Button>
          </div>
        </FormSurface>
      </section>

      <section aria-labelledby="mcp-tokens-heading" className="grid min-w-0 gap-3">
        <div>
          <h2 className="text-lg font-semibold" id="mcp-tokens-heading">{t("mcp.tokens")}</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">{t("mcp.tokensHint")}</p>
        </div>
        {!tokens.data?.length ? <EmptyPanel title={t("mcp.noTokens")} description={t("mcp.noTokensHint")} /> : (
          <>
            <DataTableFrame className="hidden lg:block">
              <Table.Content aria-label={t("mcp.tokens")}>
                <Table.Header>
                  <Table.Column isRowHeader>{t("mcp.tokenName")}</Table.Column>
                  <Table.Column>{t("mcp.permission")}</Table.Column>
                  <Table.Column>{t("common.status")}</Table.Column>
                  <Table.Column>{t("common.created")}</Table.Column>
                  <Table.Column>{t("mcp.lastUsed")}</Table.Column>
                  <Table.Column>{t("common.actions")}</Table.Column>
                </Table.Header>
                <Table.Body>
                  {tokens.data.map((token) => (
                    <Table.Row key={token.id}>
                      <Table.Cell>
                        <div className="grid gap-1">
                          <strong className="text-sm">{token.name}</strong>
                          <code className="text-xs text-muted">{token.id}</code>
                        </div>
                      </Table.Cell>
                      <Table.Cell>
                        <Chip color={token.permission === "manage" ? "warning" : "accent"} size="sm" variant="soft">
                          {t(`mcp.permissions.${token.permission}`)}
                        </Chip>
                      </Table.Cell>
                      <Table.Cell><TokenStatusChips token={token} /></Table.Cell>
                      <Table.Cell className="text-xs text-muted">{formatDateTime(token.created_at, i18n.language)}</Table.Cell>
                      <Table.Cell className="text-xs text-muted">{formatDateTime(token.last_used_at, i18n.language)}</Table.Cell>
                      <Table.Cell>
                        <Button
                          isDisabled={!token.active}
                          size="sm"
                          variant="danger-soft"
                          onPress={() => setRevoking(token)}
                        >
                          <IconTrash aria-hidden="true" size={16} />
                          {t("mcp.revoke")}
                        </Button>
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Content>
            </DataTableFrame>
            <div className="grid gap-3 lg:hidden">
              {tokens.data.map((token) => (
                <Surface className="data-mobile-card grid gap-3 rounded-lg border border-border p-4" key={token.id}>
                  <div className="flex min-w-0 items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate font-semibold">{token.name}</h3>
                      <code className="mt-1 block truncate text-xs text-muted">{token.id}</code>
                    </div>
                    <Chip color={token.permission === "manage" ? "warning" : "accent"} size="sm" variant="soft">
                      {t(`mcp.permissions.${token.permission}`)}
                    </Chip>
                  </div>
                  <TokenStatusChips token={token} />
                  <dl className="grid gap-2 border-t border-border pt-3 text-xs sm:grid-cols-2">
                    <div>
                      <dt className="text-muted">{t("common.created")}</dt>
                      <dd className="mt-1">{formatDateTime(token.created_at, i18n.language)}</dd>
                    </div>
                    <div>
                      <dt className="text-muted">{t("mcp.lastUsed")}</dt>
                      <dd className="mt-1">{formatDateTime(token.last_used_at, i18n.language)}</dd>
                    </div>
                  </dl>
                  <Button
                    className="w-full"
                    isDisabled={!token.active}
                    variant="danger-soft"
                    onPress={() => setRevoking(token)}
                  >
                    <IconTrash aria-hidden="true" size={17} />
                    {t("mcp.revoke")}
                  </Button>
                </Surface>
              ))}
            </div>
          </>
        )}
      </section>

      <section aria-labelledby="mcp-clients-heading" className="grid min-w-0 gap-3">
        <div>
          <h2 className="text-lg font-semibold" id="mcp-clients-heading">{t("mcp.clientConfiguration")}</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">{t("mcp.clientConfigurationHint")}</p>
        </div>
        <FormSurface className="min-w-0">
          <Tabs
            aria-label={t("mcp.clientConfiguration")}
            className="min-w-0"
            selectedKey={client}
            variant="secondary"
            onSelectionChange={(key) => setClient(String(key) as MCPClientKey)}
          >
            <Tabs.ListContainer>
              <Tabs.List>
                {mcpClientKeys.map((key) => (
                  <Tabs.Tab id={key} key={key}>
                    {t(`mcp.clients.${key}`)}
                    <Tabs.Indicator />
                  </Tabs.Tab>
                ))}
              </Tabs.List>
            </Tabs.ListContainer>
            {mcpClientKeys.map((key) => (
              <Tabs.Panel className="min-w-0 pt-4" id={key} key={key}>
                <div className="overflow-hidden rounded-lg border border-border bg-surface">
                  <div className="flex items-center justify-between gap-3 border-b border-border px-3 py-2">
                    <span className="flex items-center gap-2 text-xs font-semibold text-muted">
                      <IconCode aria-hidden="true" size={15} />
                      {key === "codex" ? "TOML" : "JSON"}
                    </span>
                    <Button size="sm" variant="ghost" onPress={() => void copy(mcpClientConfiguration(key, endpoint), t(`mcp.clients.${key}`))}>
                      <IconCopy aria-hidden="true" size={15} />
                      {t("mcp.copyConfiguration")}
                    </Button>
                  </div>
                  <pre
                    aria-label={t(`mcp.clients.${key}`)}
                    className="max-h-96 overflow-auto p-4 text-xs leading-6 outline-none focus-visible:ring-2 focus-visible:ring-accent"
                    tabIndex={0}
                  >
                    <code>{mcpClientConfiguration(key, endpoint)}</code>
                  </pre>
                </div>
              </Tabs.Panel>
            ))}
          </Tabs>
        </FormSurface>
      </section>

      <section aria-labelledby="mcp-tools-heading" className="grid min-w-0 gap-3">
        <div>
          <h2 className="text-lg font-semibold" id="mcp-tools-heading">{t("mcp.toolCatalog")}</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">{t("mcp.toolCatalogHint")}</p>
        </div>
        <FormSurface className="grid gap-3 p-3 md:grid-cols-[minmax(0,1fr)_15rem]">
          <SearchField
            aria-label={t("mcp.searchTools")}
            value={toolSearch}
            variant="secondary"
            onChange={setToolSearch}
          >
            <SearchField.Group>
              <SearchField.SearchIcon><IconSearch aria-hidden="true" size={16} /></SearchField.SearchIcon>
              <SearchField.Input placeholder={t("mcp.searchTools")} />
              <SearchField.ClearButton aria-label={t("common.clearSearch")} />
            </SearchField.Group>
          </SearchField>
          <SelectField
            label={t("mcp.permissionFilter")}
            options={scopeOptions}
            value={scopeFilter}
            onChange={(value) => setScopeFilter(value as ToolScopeFilter)}
          />
        </FormSurface>
        {!toolGroups.length ? <EmptyPanel title={t("mcp.noTools")} /> : (
          <Accordion allowsMultipleExpanded className="min-w-0" hideSeparator={false}>
            {toolGroups.map(([category, categoryTools]) => (
              <Accordion.Item
                defaultExpanded={expandToolGroups}
                id={category}
                key={`${category}:${expandToolGroups ? "expanded" : "collapsed"}`}
              >
                <Accordion.Heading>
                  <Accordion.Trigger>
                    <span className="flex min-w-0 flex-1 items-center gap-2 text-left">
                      <span className="truncate text-sm font-semibold">
                        {t(`mcp.categories.${category}`, { defaultValue: category })}
                      </span>
                      <Chip size="sm" variant="soft">{categoryTools.length}</Chip>
                    </span>
                    <Accordion.Indicator />
                  </Accordion.Trigger>
                </Accordion.Heading>
                <Accordion.Panel>
                  <Accordion.Body>
                    <div className="grid gap-2 pb-2">
                      {categoryTools.map((tool) => (
                        <Surface className="grid min-w-0 gap-3 rounded-lg border border-border p-4 md:grid-cols-[minmax(12rem,0.8fr)_minmax(0,1.4fr)_auto] md:items-center" key={tool.name}>
                          <div className="min-w-0">
                            <code className="break-all text-sm font-semibold text-[var(--accent-strong)]">{tool.name}</code>
                            <p className="mt-1 text-xs text-muted">{tool.operation_id}</p>
                          </div>
                          <p className="text-sm leading-relaxed text-muted">
                            {t(`mcp.toolDescriptions.${tool.name}`, { defaultValue: tool.description })}
                          </p>
                          <div className="flex flex-wrap gap-1.5 md:max-w-44 md:justify-end">
                            <Chip color={tool.scope === "mcp:write" ? "warning" : "accent"} size="sm" variant="soft">
                              {t(tool.scope === "mcp:write" ? "mcp.permissions.manage" : "mcp.permissions.read")}
                            </Chip>
                            <Chip color={safetyColor(tool.safety)} size="sm" variant="soft">
                              {t(`mcp.safety.${tool.safety}`)}
                            </Chip>
                            {tool.open_world ? (
                              <Chip color="warning" size="sm" variant="soft">
                                <IconWorld aria-hidden="true" size={13} />
                                {t("mcp.openWorld")}
                              </Chip>
                            ) : null}
                          </div>
                        </Surface>
                      ))}
                    </div>
                  </Accordion.Body>
                </Accordion.Panel>
              </Accordion.Item>
            ))}
          </Accordion>
        )}
      </section>

      <FormModal
        open={createOpen}
        title={t("mcp.createToken")}
        onOpenChange={(open) => {
          setCreateOpen(open);
          if (!open) resetCreateForm();
        }}
        actions={(
          <>
            <Button variant="ghost" onPress={() => setCreateOpen(false)}>
              <IconX aria-hidden="true" size={17} />
              {t("common.cancel")}
            </Button>
            <Button isPending={saving} type="submit" variant="primary" form="mcp-token-form">
              <IconKey aria-hidden="true" size={17} />
              {t("mcp.createToken")}
            </Button>
          </>
        )}
      >
        <form className="grid gap-5" id="mcp-token-form" onSubmit={(event) => void createToken(event)}>
          <FormField
            isRequired
            icon={IconKey}
            label={t("mcp.tokenName")}
            description={t("mcp.tokenNameHint")}
            value={name}
            onChange={setName}
          />
          <PasswordField
            isRequired
            icon={IconShieldLock}
            label={t("mcp.password")}
            description={t("mcp.passwordHint")}
            value={password}
            onChange={setPassword}
          />
          <SelectField
            icon={IconKey}
            label={t("mcp.permission")}
            options={permissionSelectOptions}
            value={permission}
            onChange={(value) => setPermission(value as "read" | "manage")}
          />
          <SelectField
            icon={IconClock}
            label={t("mcp.expiry")}
            options={expiryOptions}
            value={expiry}
            onChange={(value) => setExpiry(value as (typeof expiryValues)[number])}
          />
          {expiry === "never" ? (
            <Surface className="flex items-start gap-3 rounded-lg border border-warning-soft-border bg-warning-soft p-4 text-warning-soft-foreground">
              <IconAlertTriangle aria-hidden="true" className="mt-0.5 shrink-0" size={19} />
              <p className="text-sm leading-relaxed">{t("mcp.permanentWarning")}</p>
            </Surface>
          ) : null}
        </form>
      </FormModal>

      <ConfirmModal
        open={Boolean(createdToken)}
        title={t("mcp.createdTitle")}
        onOpenChange={(open) => {
          if (!open) setCreatedToken(null);
        }}
        actions={(
          <Button variant="primary" onPress={() => setCreatedToken(null)}>
            <IconCheck aria-hidden="true" size={17} />
            {t("common.confirm")}
          </Button>
        )}
        size="lg"
      >
        {createdToken ? (
          <div className="grid gap-4">
            <Surface className="flex items-start gap-3 rounded-lg border border-warning-soft-border bg-warning-soft p-4 text-warning-soft-foreground">
              <IconAlertTriangle aria-hidden="true" className="mt-0.5 shrink-0" size={19} />
              <p className="text-sm leading-relaxed">{t("mcp.createdBody")}</p>
            </Surface>
            <div className="grid min-w-0 gap-2">
              <span className="text-sm font-semibold">{t("mcp.tokenSecret")}</span>
              <code className="max-h-32 overflow-auto break-all rounded-lg border border-border bg-default p-4 text-xs leading-relaxed">{createdToken.token}</code>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="primary" onPress={() => void copy(createdToken.token, t("mcp.tokenSecret"))}>
                <IconCopy aria-hidden="true" size={17} />
                {t("mcp.copyToken")}
              </Button>
              <Button variant="outline" onPress={() => void copy(mcpReadyConfiguration(endpoint, createdToken.token), t("mcp.readyConfiguration"))}>
                <IconCode aria-hidden="true" size={17} />
                {t("mcp.copyReadyConfiguration")}
              </Button>
            </div>
          </div>
        ) : null}
      </ConfirmModal>

      <ConfirmModal
        open={Boolean(revoking)}
        title={t("mcp.revokeTitle")}
        onOpenChange={(open) => {
          if (!open) setRevoking(null);
        }}
        actions={(
          <>
            <Button variant="ghost" onPress={() => setRevoking(null)}>
              <IconX aria-hidden="true" size={17} />
              {t("common.cancel")}
            </Button>
            <Button isPending={saving} variant="danger" onPress={() => void revokeToken()}>
              <IconTrash aria-hidden="true" size={17} />
              {t("mcp.revoke")}
            </Button>
          </>
        )}
      >
        <p className="text-sm leading-relaxed text-muted">{t("mcp.revokeBody", { name: revoking?.name })}</p>
      </ConfirmModal>
    </div>
  );
}
