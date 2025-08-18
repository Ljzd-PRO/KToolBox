export interface TaskResponse {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
  progress?: Record<string, any>;
}

export interface SearchCreatorRequest {
  name?: string;
  id?: string;
  service?: string;
}

export interface SearchCreatorPostRequest {
  id?: string;
  name?: string;
  service?: string;
  q?: string;
  o?: number;
}

export interface GetPostRequest {
  service: string;
  creator_id: string;
  post_id: string;
  revision_id?: string;
}

export interface DownloadPostRequest {
  url?: string;
  service?: string;
  creator_id?: string;
  post_id?: string;
  revision_id?: string;
  path?: string;
  dump_post_data?: boolean;
}

export interface SyncCreatorRequest {
  url?: string;
  service?: string;
  creator_id?: string;
  path?: string;
  save_creator_indices?: boolean;
  mix_posts?: boolean;
  start_time?: string;
  end_time?: string;
  offset?: number;
  length?: number;
  keywords?: string;
  keywords_exclude?: string;
}

export interface VersionResponse {
  version: string;
}

export interface SiteVersionResponse {
  site_version: string;
}

export interface ExampleEnvResponse {
  env_content: string;
}