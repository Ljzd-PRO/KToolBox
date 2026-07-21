import { Alert, Button, Chip, Surface, Table, toast } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconChevronDown as ChevronDown,
  IconChevronUp as ChevronUp,
  IconCloud as Cloud,
  IconDownload as Download,
  IconEye as Eye,
  IconFileSearch as FileSearch,
  IconFolder as FolderOutput,
  IconHistory as History,
  IconJson as FileJson,
  IconList as ListStart,
  IconSearch as Search,
  IconUser as UserRound,
  IconX as X,
} from "@tabler/icons-react";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import {
  DataTableFrame,
  EmptyPanel,
  FormField,
  FormModal,
  FormSwitchField,
  FormSurface,
  IconButton,
  NumberInput,
  PageHeader,
  PageLoading,
  SelectField,
} from "../components/ui";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatDateTime } from "../lib/format";
import { downloadTaskTargetKey } from "../lib/taskPresentation";
import type { DownloadTaskSpec, PawchivePost, PawchiveRevision, TaskRecord } from "../types";

export function PostsPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [service, setService] = useState("fanbox");
  const [creatorId, setCreatorId] = useState("");
  const [creatorName, setCreatorName] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [results, setResults] = useState<PawchivePost[]>([]);
  const [searched, setSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState<PawchivePost | null>(null);
  const [selectedRevision, setSelectedRevision] = useState("");
  const [showContent, setShowContent] = useState(false);
  const [output, setOutput] = useState("downloads");
  const [dumpMetadata, setDumpMetadata] = useState(true);
  const [creating, setCreating] = useState(false);

  const detailsQuery = useQuery({
    queryKey: ["post-details", selected?.service, selected?.user, selected?.id, selectedRevision],
    queryFn: () => api<PawchivePost | PawchiveRevision>(
      `/pawchive/posts/${selected?.service}/${selected?.user}/${selected?.id}${selectedRevision ? `?revision_id=${encodeURIComponent(selectedRevision)}` : ""}`,
    ),
    enabled: Boolean(selected),
  });
  const revisionsQuery = useQuery({
    queryKey: ["post-revisions", selected?.service, selected?.user, selected?.id],
    queryFn: () => api<PawchiveRevision[]>(`/pawchive/posts/${selected?.service}/${selected?.user}/${selected?.id}/revisions`),
    enabled: Boolean(selected),
  });

  async function searchPosts(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearching(true);
    try {
      const parameters = new URLSearchParams();
      if (service.trim()) parameters.set("service", service.trim());
      if (creatorId.trim()) parameters.set("creator_id", creatorId.trim());
      if (creatorName.trim()) parameters.set("name", creatorName.trim());
      if (query.trim()) parameters.set("query", query.trim());
      if (offset) parameters.set("offset", String(offset));
      setResults(await api<PawchivePost[]>(`/pawchive/posts?${parameters.toString()}`));
      setSearched(true);
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSearching(false);
    }
  }

  function openPost(post: PawchivePost) {
    setSelected(post);
    setSelectedRevision("");
    setShowContent(false);
    setOutput("downloads");
    setDumpMetadata(true);
  }

  async function createDownload() {
    if (!session || !selected) return;
    setCreating(true);
    try {
      const revisionId = selectedRevision || null;
      const spec: DownloadTaskSpec = {
        kind: "download",
        service: selected.service,
        creator_id: selected.user,
        post_id: selected.id,
        revision_id: revisionId,
        output,
        dump_post_data: dumpMetadata,
      };
      const title = detailsQuery.data?.title ?? selected.title;
      const snapshotCreatorName = creatorName.trim() || null;
      const task = await api<TaskRecord>("/tasks", {
        method: "POST",
        csrfToken: session.csrf_token,
        body: {
          spec,
          presentation: title || snapshotCreatorName
            ? {
                target_key: downloadTaskTargetKey(selected.service, selected.user, selected.id, revisionId),
                title: title || null,
                creator_name: snapshotCreatorName,
              }
            : null,
        },
      });
      await queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success(t("tasks.created"));
      setSelected(null);
      navigate(`/tasks/${task.id}`);
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setCreating(false);
    }
  }

  const details = detailsQuery.data ?? selected;
  const revisionOptions = [
    { value: "", label: t("posts.currentRevision") },
    ...(revisionsQuery.data ?? []).map((revision) => ({
      value: String(revision.revision_id),
      label: t("posts.revisionLabel", { id: revision.revision_id }),
    })),
  ];

  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-6">
      <PageHeader description={t("posts.description")} title={t("posts.title")} />
      <FormSurface>
        <form className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" onSubmit={searchPosts}>
          <FormField icon={Cloud} label={t("posts.service")} value={service} onChange={setService} />
          <FormField icon={UserRound} label={t("posts.creatorId")} value={creatorId} onChange={setCreatorId} />
          <FormField icon={UserRound} label={t("posts.creatorName")} value={creatorName} onChange={setCreatorName} />
          <NumberInput icon={ListStart} label={t("tasks.offset")} minValue={0} step={50} value={offset} onChange={setOffset} />
          <div className="md:col-span-2 xl:col-span-3">
            <FormField icon={Search} label={t("posts.query")} value={query} onChange={setQuery} />
          </div>
          <div className="flex items-end justify-end">
            <Button className="w-full md:w-auto" isPending={searching} type="submit" variant="primary">
              <Search aria-hidden="true" size={17} />
              {t("posts.search")}
            </Button>
          </div>
        </form>
      </FormSurface>

      <section className="grid gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">{t("posts.results")}</h2>
          <Chip color="accent" size="sm" variant="soft">{results.length}</Chip>
        </div>
        {searched && !results.length ? <EmptyPanel title={t("posts.empty")} /> : null}
        {!searched ? <EmptyPanel description={t("posts.searchHint")} title={t("posts.searchReady")} /> : null}
        {results.length ? (
          <>
            <DataTableFrame className="hidden md:block">
              <Table.Content aria-label={t("posts.results")}>
                    <Table.Header>
                      <Table.Column isRowHeader>{t("posts.post")}</Table.Column>
                      <Table.Column>{t("posts.creatorId")}</Table.Column>
                      <Table.Column>{t("posts.service")}</Table.Column>
                      <Table.Column>{t("posts.published")}</Table.Column>
                      <Table.Column>{t("common.actions")}</Table.Column>
                    </Table.Header>
                    <Table.Body>
                      {results.map((post) => (
                        <Table.Row id={`${post.service}:${post.user}:${post.id}`} key={`${post.service}:${post.user}:${post.id}`}>
                          <Table.Cell><p className="max-w-md truncate font-medium">{post.title || `#${post.id}`}</p></Table.Cell>
                          <Table.Cell><code className="text-xs">{post.user}</code></Table.Cell>
                          <Table.Cell><Chip size="sm" variant="soft">{post.service}</Chip></Table.Cell>
                          <Table.Cell className="text-xs text-muted">{formatDateTime(post.published, i18n.language)}</Table.Cell>
                          <Table.Cell><IconButton icon={Eye} label={t("posts.details")} onPress={() => openPost(post)} /></Table.Cell>
                        </Table.Row>
                      ))}
                    </Table.Body>
              </Table.Content>
            </DataTableFrame>
            <div className="grid gap-3 md:hidden">
              {results.map((post) => (
                <Surface className="data-mobile-card grid gap-3 rounded-lg border border-border p-4" key={`${post.service}:${post.user}:${post.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0"><p className="truncate font-medium">{post.title || `#${post.id}`}</p><p className="mt-1 text-xs text-muted">{post.service}:{post.user}</p></div>
                    <IconButton icon={Eye} label={t("posts.details")} onPress={() => openPost(post)} />
                  </div>
                  <p className="text-xs text-muted">{formatDateTime(post.published, i18n.language)}</p>
                </Surface>
              ))}
            </div>
          </>
        ) : null}
      </section>

      <FormModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setSelected(null)}><X aria-hidden="true" size={17} />{t("common.close")}</Button>
            <Button isPending={creating} variant="primary" onPress={() => void createDownload()}>
              <Download aria-hidden="true" size={17} />
              {t("posts.createDownload")}
            </Button>
          </>
        }
        open={selected !== null}
        size="lg"
        title={details?.title || (details ? `#${details.id}` : t("posts.details"))}
        onOpenChange={(open) => !open && setSelected(null)}
      >
        {detailsQuery.isLoading ? <PageLoading /> : details ? (
          <div className="grid gap-5">
            <div className="flex flex-wrap gap-2">
              <Chip color="accent" size="sm" variant="soft">{details.service}</Chip>
              <Chip size="sm" variant="soft">{details.user}:{details.id}</Chip>
              {"revision_id" in details ? <Chip color="warning" size="sm" variant="soft">{t("posts.revisionLabel", { id: details.revision_id })}</Chip> : null}
            </div>
            <section className="grid gap-4 border-t border-border pt-5">
              <SelectField icon={History} label={t("posts.revision")} options={revisionOptions} value={selectedRevision} onChange={setSelectedRevision} />
              <FormField icon={FolderOutput} isRequired label={t("tasks.output")} value={output} onChange={setOutput} />
              <FormSwitchField icon={FileJson} isSelected={dumpMetadata} label={t("tasks.dumpMetadata")} onChange={setDumpMetadata} />
            </section>
            <Alert status="warning">
              <Alert.Indicator><FileSearch aria-hidden="true" size={18} /></Alert.Indicator>
              <Alert.Content><Alert.Title>{t("posts.mediaSafeTitle")}</Alert.Title><Alert.Description>{t("posts.mediaSafeBody")}</Alert.Description></Alert.Content>
            </Alert>
            <div className="grid gap-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium">{t("posts.contentHidden")}</span>
                <Button size="sm" variant="ghost" onPress={() => setShowContent((value) => !value)}>
                  {showContent ? <ChevronUp aria-hidden="true" size={16} /> : <ChevronDown aria-hidden="true" size={16} />}
                  {showContent ? t("posts.hideContent") : t("posts.showContent")}
                </Button>
              </div>
              {showContent ? <div className="max-h-64 overflow-y-auto whitespace-pre-wrap break-words rounded-lg bg-default p-4 text-sm leading-relaxed">{details.content || t("common.none")}</div> : null}
            </div>
          </div>
        ) : null}
      </FormModal>
    </div>
  );
}
