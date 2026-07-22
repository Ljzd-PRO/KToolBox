import {
  Breadcrumbs,
  Button,
  Chip,
  Description,
  EmptyState,
  FieldError,
  Input,
  InputGroup,
  Label,
  ListBox,
  Modal,
  SearchField,
  Select,
  Spinner,
  Surface,
  Switch,
  TextField,
  Tooltip,
  useOverlayState,
} from "@heroui/react";
import {
  IconAlertTriangle as AlertTriangle,
  IconArrowRight as ArrowRight,
  IconArrowUp as ArrowUp,
  IconChevronDown as ChevronDown,
  IconChevronRight as ChevronRight,
  IconCircleCheck as CircleCheck,
  IconEye as Eye,
  IconFile as File,
  IconFileUnknown as FileUnknown,
  IconFolder as Folder,
  IconFolderCheck as FolderCheck,
  IconFolderOpen as FolderOpen,
  IconFolderPlus as FolderPlus,
  IconHome as Home,
  IconRefresh as Refresh,
  IconSearch as Search,
  IconServer as Server,
  IconTrash as Trash,
  IconX as X,
  type TablerIcon,
} from "@tabler/icons-react";
import type { TFunction } from "i18next";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { useTranslation } from "react-i18next";

import { api, ApiError, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { FilesystemBrowse, FilesystemEntry, PathSelector } from "../types";
import { ConfirmModal, FormModal } from "./ui";

type RemotePathFieldProps = {
  label: string;
  description?: string;
  value: string;
  onChange: (value: string) => void;
  selector: PathSelector;
  placeholder?: string;
  icon?: TablerIcon;
  isRequired?: boolean;
  isDisabled?: boolean;
  isReadOnly?: boolean;
  isInvalid?: boolean;
  errorMessage?: string;
};

type LoadOptions = {
  path?: string;
  search?: string;
  includeHidden?: boolean;
  offset?: number;
  append?: boolean;
  initial?: boolean;
};

export function RemotePathField({
  label,
  description,
  value,
  onChange,
  selector,
  placeholder,
  icon: Icon,
  isRequired,
  isDisabled,
  isReadOnly,
  isInvalid,
  errorMessage,
}: RemotePathFieldProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const browseButton = useRef<HTMLButtonElement>(null);
  const browseLabel = t("pathPicker.browse", { label });

  function closePicker() {
    setOpen(false);
    window.setTimeout(() => browseButton.current?.focus(), 0);
  }

  return (
    <>
      <TextField.Root
        className="grid gap-1.5"
        fullWidth
        isDisabled={isDisabled}
        isInvalid={isInvalid}
        isReadOnly={isReadOnly}
        isRequired={isRequired}
        value={value}
        variant="secondary"
        onChange={onChange}
      >
        <Label className="field-label flex min-w-0 flex-1 items-center gap-1.5 text-sm font-semibold text-[var(--text-secondary)]">
          {Icon ? <Icon aria-hidden="true" className="field-label-icon shrink-0" size={15} stroke={1.8} /> : null}
          <span className="min-w-0 break-words leading-snug">{label}</span>
        </Label>
        <InputGroup fullWidth variant="secondary">
          <InputGroup.Input className="font-mono text-[0.8125rem]" placeholder={placeholder} />
          <InputGroup.Suffix className="p-1">
            <Tooltip>
              <Button
                isIconOnly
                aria-label={browseLabel}
                className="size-9 min-w-9"
                isDisabled={isDisabled || isReadOnly}
                ref={browseButton}
                type="button"
                variant="ghost"
                onPress={() => setOpen(true)}
              >
                <FolderOpen aria-hidden="true" size={17} stroke={1.8} />
              </Button>
              <Tooltip.Content>{browseLabel}</Tooltip.Content>
            </Tooltip>
          </InputGroup.Suffix>
        </InputGroup>
        {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
        {errorMessage ? <FieldError>{errorMessage}</FieldError> : null}
      </TextField.Root>
      {open ? (
        <RemotePathPicker
          initialValue={value}
          key={`${selector.scope}:${selector.kind}:${selector.value_mode}:${value}`}
          open
          selector={selector}
          title={label}
          onCancel={closePicker}
          onSelect={(nextValue) => {
            onChange(nextValue);
            closePicker();
          }}
        />
      ) : null}
    </>
  );
}

export function RemotePathPicker({
  open,
  title,
  initialValue,
  selector,
  onCancel,
  onSelect,
}: {
  open: boolean;
  title: string;
  initialValue: string;
  selector: PathSelector;
  onCancel: () => void;
  onSelect: (value: string) => void;
}) {
  const { t } = useTranslation();
  const auth = useAuth(false);
  const state = useOverlayState({ isOpen: open, onOpenChange: (next) => !next && onCancel() });
  const [data, setData] = useState<FilesystemBrowse | null>(null);
  const dataRef = useRef<FilesystemBrowse | null>(null);
  const requestRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const [address, setAddress] = useState(initialValue);
  const [search, setSearch] = useState("");
  const [includeHidden, setIncludeHidden] = useState(false);
  const [fileName, setFileName] = useState("");
  const [newFolderName, setNewFolderName] = useState("");
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<FilesystemEntry | null>(null);
  const [deletingFolder, setDeletingFolder] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const requestBrowse = useCallback(
    async (options: LoadOptions, signal: AbortSignal) => {
      const parameters = new URLSearchParams({
        scope: selector.scope,
        mode: selector.kind,
        search: options.search ?? "",
        include_hidden: String(options.includeHidden ?? false),
        offset: String(options.offset ?? 0),
        limit: "100",
      });
      if (options.path) parameters.set("path", options.path);
      return api<FilesystemBrowse>(`/filesystem?${parameters.toString()}`, { signal });
    },
    [selector.kind, selector.scope],
  );

  const load = useCallback(
    async (options: LoadOptions = {}) => {
      const requestId = ++requestRef.current;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      const hasData = dataRef.current !== null;
      setLoading(!hasData);
      setRefreshing(hasData);
      setError(null);
      try {
        let response: FilesystemBrowse;
        try {
          response = await requestBrowse(options, controller.signal);
        } catch (requestError) {
          const canFallback = options.initial && options.path && requestError instanceof ApiError && [403, 404, 422].includes(requestError.status);
          if (!canFallback) throw requestError;
          response = await requestBrowse({ ...options, path: undefined, initial: false }, controller.signal);
          const fallbackName = leafName(options.path ?? "", response.separator);
          if (selector.kind === "file") setFileName(fallbackName);
          else setNewFolderName(fallbackName);
          setNotice(t("pathPicker.fallbackNotice"));
        }
        if (requestId !== requestRef.current) return;
        const next = options.append && dataRef.current
          ? { ...response, entries: [...dataRef.current.entries, ...response.entries] }
          : response;
        dataRef.current = next;
        setData(next);
        setAddress(response.path);
        if (!options.append) {
          if (selector.kind === "file" && response.suggested_name) setFileName(response.suggested_name);
          if (selector.kind === "directory" && response.suggested_name) {
            setNewFolderName(response.suggested_name);
            setShowNewFolder(true);
          }
        }
      } catch (requestError) {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
        if (requestId === requestRef.current) setError(filesystemErrorText(requestError, t));
      } finally {
        if (requestId === requestRef.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [requestBrowse, selector.kind, t],
  );

  useEffect(() => {
    void load({ path: initialValue || undefined, initial: true });
    return () => abortRef.current?.abort();
  }, [initialValue, load]);

  useEffect(() => {
    if (!open || !dataRef.current) return;
    const timer = window.setTimeout(() => {
      void load({ path: dataRef.current?.path, search, includeHidden });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [includeHidden, load, open, search]);

  const selectedValue = useMemo(() => {
    if (!data) return null;
    if (selector.kind === "directory") {
      return selector.value_mode === "project_relative" ? data.project_relative_path : data.path;
    }
    if (!validLeafName(fileName, data.separator)) return null;
    const base = selector.value_mode === "project_relative" ? data.project_relative_path : data.path;
    if (base == null) return null;
    if (selector.value_mode === "project_relative" && base === ".") return fileName;
    return `${base}${base.endsWith(data.separator) ? "" : data.separator}${fileName}`;
  }, [data, fileName, selector.kind, selector.value_mode]);

  function navigate(path: string) {
    setSearch("");
    setNotice(null);
    setShowNewFolder(false);
    setNewFolderName("");
    setCreateError(null);
    if (selector.kind === "file") setFileName("");
    void load({ path, includeHidden });
  }

  function activateEntry(entry: FilesystemEntry) {
    if (entry.kind === "directory" && entry.navigable) {
      navigate(entry.path);
    } else if (selector.kind === "file" && entry.kind === "file") {
      setFileName(entry.name);
    }
  }

  async function createFolder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    event.stopPropagation();
    if (!data || !validLeafName(newFolderName, data.separator)) {
      setCreateError(t("pathPicker.invalidName"));
      return;
    }
    const csrfToken = auth?.session?.csrf_token;
    if (!csrfToken) {
      setCreateError(t("pathPicker.sessionRequired"));
      return;
    }
    setCreatingFolder(true);
    setCreateError(null);
    try {
      const entry = await api<FilesystemEntry>("/filesystem/directories", {
        method: "POST",
        csrfToken,
        body: { scope: selector.scope, parent: data.path, name: newFolderName },
      });
      setShowNewFolder(false);
      setNewFolderName("");
      setSearch("");
      await load({ path: entry.path, includeHidden });
      setNotice(t("pathPicker.folderCreated", { name: entry.name }));
    } catch (requestError) {
      setCreateError(filesystemErrorText(requestError, t));
    } finally {
      setCreatingFolder(false);
    }
  }

  async function deleteFolder() {
    if (!deleteTarget) return;
    const csrfToken = auth?.session?.csrf_token;
    if (!csrfToken) {
      setDeleteError(t("pathPicker.sessionRequired"));
      return;
    }
    setDeletingFolder(true);
    setDeleteError(null);
    try {
      await api<void>("/filesystem/directories", {
        method: "DELETE",
        csrfToken,
        body: { scope: selector.scope, path: deleteTarget.path },
      });
      const deletedName = deleteTarget.name;
      setDeleteTarget(null);
      await load({ path: dataRef.current?.path, search, includeHidden });
      setNotice(t("pathPicker.folderDeleted", { name: deletedName }));
    } catch (requestError) {
      setDeleteError(filesystemErrorText(requestError, t));
    } finally {
      setDeletingFolder(false);
    }
  }

  function submitAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    event.stopPropagation();
    navigate(address);
  }

  function submitSearch(event: KeyboardEvent<HTMLInputElement>) {
    if (event.nativeEvent.isComposing || event.key !== "Enter") return;
    event.preventDefault();
    void load({ path: dataRef.current?.path, search, includeHidden });
  }

  const selectedLocation = data?.locations
    .filter((location) => data && pathContains(data.path, location.path, data.separator))
    .sort((left, right) => right.path.length - left.path.length)[0]?.id ?? null;
  const currentLocation = data?.locations.find((location) => location.id === selectedLocation) ?? null;
  const exactLocation = data?.locations.find((location) => location.path === data.path) ?? null;
  const currentFolderName = data
    ? exactLocation
      ? locationLabel(exactLocation, t)
      : leafName(data.path, data.separator) || data.path
    : t("pathPicker.location");
  const selectedFilePath = data && fileName
    ? `${data.path}${data.path.endsWith(data.separator) ? "" : data.separator}${fileName}`
    : null;
  const visibleBreadcrumbs = condenseBreadcrumbs(data?.breadcrumbs ?? []);

  return (
    <>
      <Modal state={state}>
      <Modal.Trigger aria-hidden="true" className="hidden" tabIndex={-1} />
      <Modal.Backdrop isDismissable>
        <Modal.Container className="remote-path-picker-container mx-3" placement="center" scroll="inside" size="lg">
          <Modal.Dialog className="app-modal-dialog overflow-hidden">
            <Modal.Header className="flex items-center justify-between gap-3 border-b border-border px-4 py-3 sm:px-5 sm:py-4">
              <div className="flex min-w-0 items-center gap-2">
                <Server aria-hidden="true" className="shrink-0 text-accent" size={19} stroke={1.8} />
                <Modal.Heading className="min-w-0 break-words text-base font-semibold leading-tight text-foreground sm:text-lg">{title}</Modal.Heading>
                <Chip className="hidden shrink-0 sm:inline-flex" color="accent" size="sm" variant="soft">
                  {selector.scope === "project" ? t("pathPicker.projectScope") : t("pathPicker.hostScope")}
                </Chip>
              </div>
              <Modal.CloseTrigger aria-label={t("common.close")} className="grid size-10 shrink-0 place-items-center rounded-lg text-muted hover:bg-default">
                <X aria-hidden="true" size={18} />
              </Modal.CloseTrigger>
            </Modal.Header>
            <Modal.Body className="remote-path-picker-body min-h-0 overflow-hidden p-2 sm:p-4">
              <div className="grid h-full min-h-0 grid-rows-[auto_auto_minmax(6rem,1fr)_auto] gap-2 sm:grid-rows-[auto_auto_minmax(7rem,1fr)_auto] sm:gap-3">
                <div className="grid gap-2">
                  <div className="grid min-w-0 gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
                    <Select
                      aria-label={t("pathPicker.location")}
                      fullWidth
                      selectedKey={selectedLocation}
                      variant="secondary"
                      onSelectionChange={(key) => {
                        const location = data?.locations.find((item) => item.id === key);
                        if (location) navigate(location.path);
                      }}
                    >
                      <Select.Trigger>
                        <Select.Value>{currentLocation ? locationLabel(currentLocation, t) : t("pathPicker.location")}</Select.Value>
                        <Select.Indicator><ChevronDown aria-hidden="true" size={16} /></Select.Indicator>
                      </Select.Trigger>
                      <Select.Popover>
                        <ListBox aria-label={t("pathPicker.location")}>
                          {(data?.locations ?? []).map((location) => {
                            const LocationIcon = location.id === "project" ? FolderOpen : location.id === "home" ? Home : Server;
                            const label = locationLabel(location, t);
                            return (
                              <ListBox.Item id={location.id} key={location.id} textValue={label}>
                                <LocationIcon aria-hidden="true" className="shrink-0 text-muted" size={17} stroke={1.8} />
                                <span className="min-w-0 flex-1 truncate">{label}</span>
                                <ListBox.ItemIndicator />
                              </ListBox.Item>
                            );
                          })}
                        </ListBox>
                      </Select.Popover>
                    </Select>
                    <Button
                      aria-expanded={showNewFolder}
                      isDisabled={!data || loading}
                      type="button"
                      variant="outline"
                      onPress={() => {
                        setCreateError(null);
                        setShowNewFolder((current) => !current);
                      }}
                    >
                      <FolderPlus aria-hidden="true" size={17} />
                      {t("pathPicker.newFolder")}
                    </Button>
                  </div>
                  <form className="grid min-w-0 grid-cols-[2.75rem_minmax(0,1fr)_2.75rem] gap-2 max-[359px]:grid-cols-[2.75rem_2.75rem_minmax(0,1fr)]" onSubmit={submitAddress}>
                    <Tooltip>
                      <Button isIconOnly aria-label={t("pathPicker.up")} className="size-11 min-w-11" isDisabled={!data?.parent} type="button" variant="outline" onPress={() => data?.parent && navigate(data.parent)}>
                        <ArrowUp aria-hidden="true" size={17} />
                      </Button>
                      <Tooltip.Content>{t("pathPicker.up")}</Tooltip.Content>
                    </Tooltip>
                    <TextField.Root aria-label={t("pathPicker.address")} className="min-w-0 max-[359px]:col-span-3 max-[359px]:row-start-2" fullWidth value={address} variant="secondary" onChange={setAddress}>
                      <InputGroup className="min-w-0 max-w-full overflow-hidden" fullWidth variant="secondary">
                        <InputGroup.Input className="font-mono text-xs" />
                        <InputGroup.Suffix className="p-1">
                          <Tooltip>
                            <Button
                              aria-label={t("pathPicker.go")}
                              className="h-9 min-h-9 px-2 max-sm:size-9 max-sm:min-w-9 max-sm:p-0"
                              size="sm"
                              type="submit"
                              variant="ghost"
                            >
                              <ArrowRight aria-hidden="true" size={17} />
                              <span className="max-sm:sr-only">{t("pathPicker.go")}</span>
                            </Button>
                            <Tooltip.Content>{t("pathPicker.go")}</Tooltip.Content>
                          </Tooltip>
                        </InputGroup.Suffix>
                      </InputGroup>
                    </TextField.Root>
                    <Tooltip>
                      <Button isIconOnly aria-label={t("common.refresh")} className="size-11 min-w-11" isPending={refreshing} type="button" variant="outline" onPress={() => void load({ path: dataRef.current?.path, search, includeHidden })}>
                        <Refresh aria-hidden="true" size={17} />
                      </Button>
                      <Tooltip.Content>{t("common.refresh")}</Tooltip.Content>
                    </Tooltip>
                  </form>
                  {data?.breadcrumbs.length ? (
                    <div className="min-w-0 overflow-x-auto pb-1">
                      <Breadcrumbs aria-label={t("pathPicker.breadcrumbs")} className="min-w-max">
                        {visibleBreadcrumbs.map((crumb) => {
                          const matchingLocation = data.locations.find((location) => location.path === crumb.path);
                          const label = matchingLocation ? locationLabel(matchingLocation, t) : crumb.label;
                          return (
                            <Breadcrumbs.Item
                              aria-label={crumb.collapsedLabel ? `${t("pathPicker.up")}: ${crumb.collapsedLabel}` : undefined}
                              key={crumb.path}
                              onPress={() => navigate(crumb.path)}
                            >
                              <span title={crumb.collapsedLabel ?? label}>{label}</span>
                            </Breadcrumbs.Item>
                          );
                        })}
                      </Breadcrumbs>
                    </div>
                  ) : null}
                </div>

                <div className="grid gap-2">
                  <div className="grid items-center gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
                    <SearchField aria-label={t("pathPicker.search")} value={search} variant="secondary" onChange={setSearch}>
                      <SearchField.Group>
                        <SearchField.SearchIcon><Search aria-hidden="true" size={16} /></SearchField.SearchIcon>
                        <SearchField.Input placeholder={t("pathPicker.searchPlaceholder")} onKeyDown={submitSearch} />
                        <SearchField.ClearButton aria-label={t("common.clearSearch")} />
                      </SearchField.Group>
                    </SearchField>
                    <Switch.Root
                      className="path-picker-hidden-switch min-h-11 rounded-lg border border-[var(--field-border)] bg-surface px-3 py-2 shadow-[var(--field-shadow)]"
                      isSelected={includeHidden}
                      onChange={setIncludeHidden}
                    >
                      <Switch.Content className="min-w-0 items-center gap-2.5">
                        <Switch.Control className="shrink-0"><Switch.Thumb /></Switch.Control>
                        <Label className="flex min-w-0 items-center gap-2 text-sm font-medium text-foreground">
                          <Eye aria-hidden="true" className="shrink-0 text-muted" size={16} stroke={1.8} />
                          <span className="min-w-0 break-words">{t("pathPicker.showHidden")}</span>
                        </Label>
                      </Switch.Content>
                    </Switch.Root>
                  </div>
                  {notice ? <StatusMessage tone="notice" text={notice} /> : null}
                  {error ? <StatusMessage tone="error" text={error} /> : null}
                </div>

                <Surface className="min-h-0 overflow-y-auto rounded-lg border border-border bg-surface p-1" aria-busy={loading || refreshing}>
                  {loading && !data ? (
                    <div className="grid h-full min-h-28 place-items-center"><Spinner aria-label={t("common.loading")} /></div>
                  ) : data?.entries.length ? (
                    <ListBox
                      aria-label={t("pathPicker.entries")}
                      selectedKeys={selectedFilePath ? new Set([selectedFilePath]) : new Set()}
                      selectionMode={selector.kind === "file" ? "single" : undefined}
                      onAction={(key) => {
                        const entry = data.entries.find((item) => item.path === String(key));
                        if (entry) activateEntry(entry);
                      }}
                    >
                      {data.entries.map((entry) => {
                        const disabled = entry.kind === "other" || (entry.kind === "directory" && !entry.navigable) || (selector.kind === "directory" && entry.kind === "file");
                        const EntryIcon = entry.kind === "directory" ? Folder : entry.kind === "file" ? File : FileUnknown;
                        return (
                          <ListBox.Item
                            aria-label={entry.name}
                            className="remote-path-entry min-w-0"
                            id={entry.path}
                            isDisabled={disabled}
                            key={entry.path}
                            textValue={entry.name}
                          >
                            <EntryIcon aria-hidden="true" className="shrink-0 text-muted" size={18} stroke={1.8} />
                            <span className="min-w-0 flex-1 truncate font-mono text-sm text-foreground" title={entry.name}>{entry.name}</span>
                            {entry.is_symlink ? <Chip className="shrink-0" size="sm" variant="soft">{t("pathPicker.symlink")}</Chip> : null}
                            {entry.deletable ? (
                              <Tooltip>
                                <Button
                                  isIconOnly
                                  aria-label={t("pathPicker.deleteFolder", { name: entry.name })}
                                  className="size-9 min-w-9 shrink-0 text-danger hover:bg-danger/10"
                                  size="sm"
                                  type="button"
                                  variant="ghost"
                                  onClick={(event) => event.stopPropagation()}
                                  onPress={() => {
                                    setDeleteError(null);
                                    setDeleteTarget(entry);
                                  }}
                                >
                                  <Trash aria-hidden="true" size={16} stroke={1.8} />
                                </Button>
                                <Tooltip.Content>{t("pathPicker.deleteFolder", { name: entry.name })}</Tooltip.Content>
                              </Tooltip>
                            ) : null}
                            {selector.kind === "file" ? <ListBox.ItemIndicator /> : null}
                            {entry.kind === "directory" && entry.navigable ? (
                              <ChevronRight aria-hidden="true" className="shrink-0 text-muted" size={16} />
                            ) : null}
                          </ListBox.Item>
                        );
                      })}
                    </ListBox>
                  ) : (
                    <EmptyState className="remote-path-empty-state grid h-full min-h-28 place-items-center p-4 text-center sm:p-6">
                      <div>
                        {search.trim() ? (
                          <Search aria-hidden="true" className="mx-auto text-muted" size={26} />
                        ) : (
                          <FolderOpen aria-hidden="true" className="mx-auto text-muted" size={26} />
                        )}
                        <p className="mt-3 font-medium text-foreground">
                          {t(search.trim() ? "pathPicker.empty" : "pathPicker.emptyDirectory")}
                        </p>
                        <p className="remote-path-empty-hint mt-1 text-sm text-muted">
                          {t(search.trim() ? "pathPicker.emptyHint" : "pathPicker.emptyDirectoryHint")}
                        </p>
                      </div>
                    </EmptyState>
                  )}
                  {data?.has_more ? (
                    <div className="border-t border-border p-2 text-center">
                      <Button size="sm" variant="outline" onPress={() => void load({ path: data.path, search, includeHidden, offset: data.entries.length, append: true })}>
                        {t("pathPicker.loadMore")}
                      </Button>
                    </div>
                  ) : null}
                </Surface>

                <div className="grid gap-2">
                  {selector.kind === "file" ? (
                    <TextField.Root
                      className="grid gap-1.5"
                      fullWidth
                      isInvalid={Boolean(fileName && data && !validLeafName(fileName, data.separator))}
                      value={fileName}
                      variant="secondary"
                      onChange={setFileName}
                    >
                      <Label className="text-sm font-semibold text-[var(--text-secondary)]">{t("pathPicker.fileName")}</Label>
                      <Input className="font-mono text-xs" placeholder={t("pathPicker.fileNamePlaceholder")} />
                      <Description className="text-xs text-muted">{t("pathPicker.fileNameHint")}</Description>
                      <FieldError>{t("pathPicker.invalidName")}</FieldError>
                    </TextField.Root>
                  ) : null}
                  {selectedValue ? (
                    <div className="remote-path-selection flex min-w-0 items-center gap-2 rounded-lg border border-[var(--accent-border)] bg-[var(--accent-soft)] px-3 py-2">
                      <FolderCheck aria-hidden="true" className="shrink-0 text-accent" size={17} stroke={1.8} />
                      <span className="shrink-0 text-xs font-semibold text-[var(--text-secondary)]">{t("pathPicker.currentSelection")}</span>
                      <code className="min-w-0 flex-1 truncate text-xs text-foreground" title={selectedValue}>{selectedValue}</code>
                    </div>
                  ) : null}
                </div>
              </div>
            </Modal.Body>
            <Modal.Footer className="flex flex-wrap justify-end gap-2 border-t border-border px-4 py-3 sm:px-5 sm:py-4">
              <Button type="button" variant="ghost" onPress={onCancel}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
              <Button isDisabled={!selectedValue} type="button" variant="primary" onPress={() => selectedValue && onSelect(selectedValue)}>
                <FolderOpen aria-hidden="true" size={17} />
                {selector.kind === "directory" ? t("pathPicker.selectDirectory") : t("pathPicker.selectFile")}
              </Button>
            </Modal.Footer>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
      </Modal>
      <FormModal
        actions={(
          <>
            <Button isDisabled={creatingFolder} variant="ghost" onPress={() => setShowNewFolder(false)}>
              <X aria-hidden="true" size={17} />
              {t("common.cancel")}
            </Button>
            <Button form="remote-new-folder-form" isPending={creatingFolder} type="submit" variant="primary">
              <FolderPlus aria-hidden="true" size={17} />
              {t("pathPicker.createFolder")}
            </Button>
          </>
        )}
        open={showNewFolder}
        size="sm"
        title={t("pathPicker.newFolder")}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !creatingFolder) {
            setShowNewFolder(false);
            setNewFolderName("");
            setCreateError(null);
          }
        }}
      >
        <form className="grid gap-4" id="remote-new-folder-form" onSubmit={(event) => void createFolder(event)}>
          <div className="flex min-w-0 items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-[var(--accent-soft)] text-accent">
              <FolderPlus aria-hidden="true" size={19} stroke={1.8} />
            </span>
            <p className="min-w-0 text-sm leading-relaxed text-[var(--text-secondary)]">
              {t("pathPicker.newFolderHint", { name: currentFolderName })}
            </p>
          </div>
          <TextField.Root className="grid gap-1.5" fullWidth value={newFolderName} variant="secondary" onChange={setNewFolderName}>
            <Label className="text-sm font-semibold text-[var(--text-secondary)]">{t("pathPicker.folderName")}</Label>
            <Input autoFocus placeholder={t("pathPicker.folderName")} />
          </TextField.Root>
          {createError ? <StatusMessage tone="error" text={createError} /> : null}
        </form>
      </FormModal>
      <ConfirmModal
        actions={(
          <>
            <Button isDisabled={deletingFolder} variant="ghost" onPress={() => setDeleteTarget(null)}>
              <X aria-hidden="true" size={17} />
              {t("common.cancel")}
            </Button>
            <Button isPending={deletingFolder} variant="danger" onPress={() => void deleteFolder()}>
              <Trash aria-hidden="true" size={17} />
              {t("pathPicker.deleteFolderConfirm")}
            </Button>
          </>
        )}
        open={Boolean(deleteTarget)}
        title={t("pathPicker.deleteFolderTitle")}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !deletingFolder) {
            setDeleteTarget(null);
            setDeleteError(null);
          }
        }}
      >
        <div className="grid gap-3">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            {t("pathPicker.deleteFolderBody", { name: deleteTarget?.name ?? "" })}
          </p>
          {deleteTarget ? (
            <code className="block min-w-0 break-all rounded-lg border border-border bg-default px-3 py-2 text-xs text-foreground">
              {deleteTarget.path}
            </code>
          ) : null}
          {deleteError ? <StatusMessage tone="error" text={deleteError} /> : null}
        </div>
      </ConfirmModal>
    </>
  );
}

function StatusMessage({ tone, text }: { tone: "notice" | "error"; text: string }) {
  const StatusIcon = tone === "error" ? AlertTriangle : CircleCheck;
  return (
    <div
      className={tone === "error"
        ? "flex items-start gap-2 rounded-lg border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
        : "flex items-start gap-2 rounded-lg border border-[var(--accent-border)] bg-[var(--accent-soft)] p-3 text-sm text-foreground"}
      role={tone === "error" ? "alert" : "status"}
    >
      <StatusIcon aria-hidden="true" className="mt-0.5 shrink-0" size={17} />
      <span className="min-w-0 break-words">{text}</span>
    </div>
  );
}

function leafName(path: string, separator: string): string {
  const normalized = path.replaceAll(separator === "\\" ? "/" : "\\", separator);
  return normalized.split(separator).filter(Boolean).at(-1) ?? "";
}

function validLeafName(value: string, separator: string): boolean {
  return Boolean(value) && value === value.trim() && ![".", ".."].includes(value) && ![separator, "/", "\\", "\0"].some((part) => value.includes(part));
}

function pathContains(path: string, parent: string, separator: string): boolean {
  if (path === parent) return true;
  const prefix = parent.endsWith(separator) ? parent : `${parent}${separator}`;
  return path.startsWith(prefix);
}

function condenseBreadcrumbs(
  breadcrumbs: FilesystemBrowse["breadcrumbs"],
): Array<FilesystemBrowse["breadcrumbs"][number] & { collapsedLabel?: string }> {
  if (breadcrumbs.length <= 5) return breadcrumbs;
  const collapsed = breadcrumbs[breadcrumbs.length - 4];
  return [
    breadcrumbs[0],
    { ...collapsed, label: "…", collapsedLabel: collapsed.label },
    ...breadcrumbs.slice(-3),
  ];
}

function locationLabel(location: FilesystemBrowse["locations"][number], t: TFunction): string {
  if (location.id === "project") return t("pathPicker.locations.project");
  if (location.id === "home") return t("pathPicker.locations.home");
  return location.label;
}

function filesystemErrorText(error: unknown, t: TFunction): string {
  if (error instanceof ApiError && error.detail && typeof error.detail === "object" && "code" in error.detail) {
    const code = String((error.detail as { code: unknown }).code);
    return t(`pathPicker.errors.${code}`, {
      defaultValue: t("pathPicker.errors.filesystem_error"),
    });
  }
  return errorText(error);
}
