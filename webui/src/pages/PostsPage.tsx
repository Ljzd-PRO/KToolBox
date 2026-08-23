import { Alert, Button, Chip, Surface, Table, toast } from "@heroui/react";
import type { SortDescriptor } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconChevronDown as ChevronDown,
  IconChevronUp as ChevronUp,
  IconCircleCheck as CircleCheck,
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
import { useMemo, useState, type FormEvent } from "react";
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
  MobileSortControls,
  NumberInput,
  PageHeader,
  PageLoading,
  PlatformComboBox,
  SelectField,
  SortableColumn,
} from "../components/ui";
import { RemotePathField } from "../components/RemotePathField";
import { MediaGallery, MediaViewer, WorkCover } from "../components/SensitiveMedia";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatDateTime } from "../lib/format";
import { useSensitiveMediaEnabled } from "../lib/sensitiveMedia";
import { stableSort } from "../lib/sorting";
import { TASK_OUTPUT_PATH_SELECTOR } from "../lib/pathSelectors";
import { downloadTaskTargetKey } from "../lib/taskPresentation";
import type {
  DownloadTaskSpec,
  PawchivePost,
  PawchiveRevision,
  ProjectSummary,
  TaskRecord,
} from "../types";

export function PostsPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mediaEnabled = useSensitiveMediaEnabled();
  const projectQuery = useQuery({
    queryKey: ["project"],
    queryFn: () => api<ProjectSummary>("/project"),
  });
  const [service, setService] = useState("fanbox");
  const [creatorId, setCreatorId] = useState("");
  const [creatorName, setCreatorName] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [results, setResults] = useState<PawchivePost[]>([]);
  const [visibleCount, setVisibleCount] = useState(20);
  const [searched, setSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState<PawchivePost | null>(null);
  const [selectedRevision, setSelectedRevision] = useState("");
  const [showContent, setShowContent] = useState(false);
  const [output, setOutput] = useState("");
  const [dumpMetadata, setDumpMetadata] = useState(true);
  const [creating, setCreating] = useState(false);
  const [viewer, setViewer] = useState<{ assets: NonNullable<PawchivePost["media"]>; index: number } | null>(null);
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>({
    column: "published",
    direction: "descending",
  });

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
      setVisibleCount(20);
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
    setOutput(projectQuery.data?.resolved_default_output ?? "downloads");
    setDumpMetadata(true);
    setViewer(null);
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
  const detailMedia = details?.media?.length
    ? details.media
    : details?.cover
      ? [details.cover]
      : [];
  const galleryMedia = detailMedia.filter((asset) => asset.kind !== "cover");
  const revisionOptions = [
    { value: "", label: t("posts.currentRevision"), icon: CircleCheck, tone: "success" as const },
    ...(revisionsQuery.data ?? []).map((revision) => ({
      value: String(revision.revision_id),
      label: t("posts.revisionLabel", { id: revision.revision_id }),
      icon: History,
    })),
  ];
  const sortedResults = useMemo(
    () => stableSort(
      results,
      sortDescriptor,
      (post, column) => {
        if (column === "post") return post.title || post.id;
        if (column === "creator") return post.user;
        if (column === "service") return post.service;
        return post.published ? Date.parse(String(post.published)) : null;
      },
      i18n.resolvedLanguage ?? i18n.language,
    ),
    [i18n.language, i18n.resolvedLanguage, results, sortDescriptor],
  );
  const sortOptions = [
    { value: "post", label: t("posts.post") },
    { value: "creator", label: t("posts.creatorId") },
    { value: "service", label: t("posts.service") },
    { value: "published", label: t("posts.published") },
  ];
  const visibleResults = sortedResults.slice(0, visibleCount);

  if (projectQuery.isLoading) return <PageLoading />;

  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-6">
      <PageHeader description={t("posts.description")} title={t("posts.title")} />
      <FormSurface>
        <form className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" onSubmit={searchPosts}>
          <PlatformComboBox icon={Cloud} label={t("posts.service")} value={service} onChange={setService} />
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
            <MobileSortControls
              className="lg:hidden"
              descendingByDefault={new Set(["published"])}
              descriptor={sortDescriptor}
              options={sortOptions}
              onChange={(descriptor) => descriptor && setSortDescriptor(descriptor)}
            />
            <DataTableFrame className="hidden lg:block">
              <Table.Content
                aria-label={t("posts.results")}
                sortDescriptor={sortDescriptor}
                onSortChange={setSortDescriptor}
              >
                    <Table.Header>
                      {mediaEnabled ? <Table.Column>{t("sensitiveMedia.cover")}</Table.Column> : null}
                      <SortableColumn id="post" isRowHeader>{t("posts.post")}</SortableColumn>
                      <SortableColumn id="creator">{t("posts.creatorId")}</SortableColumn>
                      <SortableColumn id="service">{t("posts.service")}</SortableColumn>
                      <SortableColumn id="published">{t("posts.published")}</SortableColumn>
                      <Table.Column>{t("common.actions")}</Table.Column>
                    </Table.Header>
                    <Table.Body>
                      {visibleResults.map((post) => (
                        <Table.Row id={`${post.service}:${post.user}:${post.id}`} key={`${post.service}:${post.user}:${post.id}`}>
                          {mediaEnabled ? (
                            <Table.Cell>
                              <WorkCover
                                asset={post.cover}
                                className="h-14 w-24 rounded-md border border-border bg-default object-cover"
                                title={post.title || `#${post.id}`}
                                onPress={post.cover ? () => setViewer({ assets: [post.cover!], index: 0 }) : undefined}
                              />
                            </Table.Cell>
                          ) : null}
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
            <div className="grid gap-3 lg:hidden">
              {visibleResults.map((post) => (
                <Surface className="data-mobile-card grid gap-3 rounded-lg border border-border p-4" key={`${post.service}:${post.user}:${post.id}`}>
                  {mediaEnabled ? (
                    <WorkCover
                      asset={post.cover}
                      className="aspect-video w-full rounded-md border border-border bg-default object-cover"
                      title={post.title || `#${post.id}`}
                      onPress={post.cover ? () => setViewer({ assets: [post.cover!], index: 0 }) : undefined}
                    />
                  ) : null}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0"><p className="truncate font-medium">{post.title || `#${post.id}`}</p><p className="mt-1 text-xs text-muted">{post.service}:{post.user}</p></div>
                    <IconButton icon={Eye} label={t("posts.details")} onPress={() => openPost(post)} />
                  </div>
                  <p className="text-xs text-muted">{formatDateTime(post.published, i18n.language)}</p>
                </Surface>
              ))}
            </div>
            {visibleCount < sortedResults.length ? (
              <div className="flex justify-center pt-1">
                <Button variant="secondary" onPress={() => setVisibleCount((count) => count + 20)}>
                  <ChevronDown aria-hidden="true" size={17} />
                  {t("common.loadMore")}
                </Button>
              </div>
            ) : null}
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
        isWide
        size="lg"
        title={details?.title || (details ? `#${details.id}` : t("posts.details"))}
        onOpenChange={(open) => !open && setSelected(null)}
      >
        {detailsQuery.isLoading ? <PageLoading /> : details ? (
          <div className={mediaEnabled && detailMedia.length ? "grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(22rem,1.1fr)]" : "grid gap-5"}>
            {mediaEnabled && details.cover ? (
              <WorkCover
                asset={details.cover}
                className="aspect-video w-full rounded-lg border border-border bg-default"
                fit="contain"
                title={details.title || `#${details.id}`}
                onPress={() => setViewer({ assets: detailMedia, index: Math.max(0, detailMedia.findIndex((asset) => asset.original_url === details.cover?.original_url)) })}
              />
            ) : null}
            <div className="grid content-start gap-5 xl:col-start-2 xl:row-span-2 xl:row-start-1">
              <div className="flex flex-wrap gap-2">
                <Chip color="accent" size="sm" variant="soft">{details.service}</Chip>
                <Chip size="sm" variant="soft">{details.user}:{details.id}</Chip>
                {"revision_id" in details ? <Chip color="warning" size="sm" variant="soft">{t("posts.revisionLabel", { id: details.revision_id })}</Chip> : null}
              </div>
              <section className="grid gap-4 border-t border-border pt-5">
                <SelectField icon={History} label={t("posts.revision")} options={revisionOptions} value={selectedRevision} onChange={setSelectedRevision} />
                <RemotePathField
                  icon={FolderOutput}
                  isRequired
                  label={t("tasks.output")}
                  selector={TASK_OUTPUT_PATH_SELECTOR}
                  value={output}
                  onChange={setOutput}
                />
                <FormSwitchField icon={FileJson} isSelected={dumpMetadata} label={t("tasks.dumpMetadata")} onChange={setDumpMetadata} />
              </section>
              {!mediaEnabled ? (
                <Alert status="warning">
                  <Alert.Indicator><FileSearch aria-hidden="true" size={18} /></Alert.Indicator>
                  <Alert.Content><Alert.Title>{t("sensitiveMedia.safeTitle")}</Alert.Title><Alert.Description>{t("sensitiveMedia.safeBody")}</Alert.Description></Alert.Content>
                </Alert>
              ) : null}
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
            {mediaEnabled && galleryMedia.length ? (
              <div className={details.cover ? "xl:col-start-1 xl:row-start-2" : "xl:col-start-1 xl:row-start-1"}>
                <MediaGallery
                  assets={galleryMedia}
                  title={details.title || `#${details.id}`}
                  onOpen={(index) => {
                    const selectedAsset = galleryMedia[index];
                    setViewer({
                      assets: detailMedia,
                      index: Math.max(0, detailMedia.findIndex((asset) => asset.original_url === selectedAsset.original_url)),
                    });
                  }}
                />
              </div>
            ) : null}
          </div>
        ) : null}
      </FormModal>
      <MediaViewer
        assets={viewer?.assets ?? []}
        index={viewer?.index ?? 0}
        open={viewer !== null}
        title={details?.title || selected?.title || t("sensitiveMedia.viewer")}
        onClose={() => setViewer(null)}
        onIndexChange={(index) => setViewer((current) => current ? { ...current, index } : current)}
      />
    </div>
  );
}
