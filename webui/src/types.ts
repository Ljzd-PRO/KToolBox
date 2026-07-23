import type { components } from "./generated/api";

export type WebUIApiSchemas = components["schemas"];

export type Session = WebUIApiSchemas["SessionResponse"];

export type ProjectSummary = WebUIApiSchemas["ProjectSummaryResponse"];

export type MCPStatus = WebUIApiSchemas["MCPStatusResponse"];

export type MCPToken = WebUIApiSchemas["MCPTokenResponse"];

export type MCPTokenCreateRequest = WebUIApiSchemas["MCPTokenCreateRequest"];

export type MCPTokenCreated = WebUIApiSchemas["MCPTokenCreatedResponse"];

export type MCPTool = WebUIApiSchemas["MCPToolResponse"];

export type CreatorReference = {
  service: string;
  creator_id: string;
  alias: string | null;
  enabled: boolean;
};

export type CreatorRosterItem = CreatorReference & {
  name: string | null;
};

export type BlockerScope = {
  mode: "global" | "creators";
  creators: string[];
};

export type FieldCondition = {
  kind: "field";
  field: string;
  operator: "contains" | "equals" | "regex" | "exists";
  values: string[];
  expected: boolean;
  case_sensitive: boolean;
  negate: boolean;
};

export type ConditionGroup = {
  kind: "group";
  mode: "any" | "all";
  conditions: Array<FieldCondition | ConditionGroup>;
  negate: boolean;
};

export type BlockerSpec = {
  id: string;
  type: string;
  enabled: boolean;
  scope: BlockerScope;
  options: { rule?: ConditionGroup } & Record<string, unknown>;
};

export type ConfigField = {
  path: string;
  env_name: string;
  section: string;
  label: string;
  description: string;
  json_schema: Record<string, unknown>;
  default: unknown;
  value: unknown;
  is_set: boolean;
  secret: boolean;
  source: string;
  apply_mode: "next_task" | "restart";
  path_selector?: PathSelector | null;
};

export type PathSelector = WebUIApiSchemas["PathSelectorResponse"];

export type FilesystemBrowse = WebUIApiSchemas["FilesystemBrowseResponse"];

export type FilesystemEntry = WebUIApiSchemas["FilesystemEntryResponse"];

export type ConfigSchema = {
  locale: "zh-CN" | "zh-Hant" | "en" | "ja" | "ko" | "fr" | "ru";
  sections: Record<string, string>;
  fields: ConfigField[];
};

export type TextDocument = {
  name: string;
  path: string;
  content: string;
  revision: string;
};

export type ProjectDocument = TextDocument & {
  configuration: {
    schema_version: 1;
    creators: CreatorReference[];
    blockers: BlockerSpec[];
  };
};

export type TaskStatus = WebUIApiSchemas["TaskStatus"];

export type DownloadTaskSpec = {
  kind: "download";
  post?: string | null;
  service?: string | null;
  creator_id?: string | null;
  post_id?: string | null;
  revision_id?: string | null;
  output: string;
  dump_post_data: boolean;
};

export type SyncTaskSpec = {
  kind: "sync";
  creators: CreatorReference[];
  output: string;
  save_creator_indices: boolean;
  mix_posts?: boolean | null;
  start_time?: string | null;
  end_time?: string | null;
  offset: number;
  length?: number | null;
  keywords: string[];
  keywords_exclude: string[];
};

export type TaskSpec = DownloadTaskSpec | SyncTaskSpec;

export type TaskPresentationSnapshot = {
  target_key: string;
  title?: string | null;
  creator_name?: string | null;
};

export type TaskCreateRequest = {
  spec: TaskSpec;
  presentation?: TaskPresentationSnapshot | null;
};

export type ActiveDownload = {
  creator_key: string;
  filename: string;
  total: number | null;
  completed: number;
  speed_bps: number;
};

export type TaskProgress = {
  queued_files: number;
  processed_files: number;
  completed_files: number;
  existing_files: number;
  failed_files: number;
  transferred_bytes: number;
  total_bytes: number | null;
  speed_bps: number;
  eta_seconds: number | null;
  active_creators: string[];
  active_downloads: Record<string, ActiveDownload>;
};

export type TaskRecord = {
  id: string;
  kind: "download" | "sync";
  status: TaskStatus;
  spec: TaskSpec;
  presentation: TaskPresentationSnapshot | null;
  position: number;
  revision: number;
  progress: TaskProgress;
  error: string | null;
  blocked_by: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskEvent = {
  id: number;
  task_id: string | null;
  event_type: string;
  data: Record<string, unknown>;
  created_at: string;
};

export type TaskAttempt = {
  id: number;
  task_id: string;
  sequence: number;
  status: TaskStatus;
  spec: TaskSpec;
  configuration: Record<string, unknown>;
  started_at: string;
  finished_at: string | null;
  error: string | null;
};

export type TaskArtifact = WebUIApiSchemas["TaskArtifact"];

export type TaskCleanupPreview = WebUIApiSchemas["TaskCleanupPreview"];

export type CreatorSummary = {
  id: string;
  service: string;
  name?: string | null;
  updated?: string | null;
};

export type PawchivePost = {
  id: string;
  service: string;
  user: string;
  title?: string | null;
  content?: string | null;
  published?: string | null;
  edited?: string | null;
  attachments?: unknown[] | null;
  [key: string]: unknown;
};

export type PawchiveRevision = PawchivePost & {
  revision_id: string | number;
};
