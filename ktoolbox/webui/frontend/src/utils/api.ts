import axios from 'axios';
import {
  TaskResponse,
  SearchCreatorRequest,
  SearchCreatorPostRequest,
  GetPostRequest,
  DownloadPostRequest,
  SyncCreatorRequest,
  VersionResponse,
  SiteVersionResponse,
  ExampleEnvResponse
} from '../types/api';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ktoolboxApi = {
  // Version endpoints
  getVersion: (): Promise<VersionResponse> =>
    api.get('/version').then(res => res.data),

  getSiteVersion: (): Promise<SiteVersionResponse> =>
    api.get('/site-version').then(res => res.data),

  getExampleEnv: (): Promise<ExampleEnvResponse> =>
    api.get('/example-env').then(res => res.data),

  // Search endpoints
  searchCreator: (request: SearchCreatorRequest): Promise<TaskResponse> =>
    api.post('/search-creator', request).then(res => res.data),

  searchCreatorPost: (request: SearchCreatorPostRequest): Promise<TaskResponse> =>
    api.post('/search-creator-post', request).then(res => res.data),

  // Post endpoints
  getPost: (request: GetPostRequest): Promise<TaskResponse> =>
    api.post('/get-post', request).then(res => res.data),

  downloadPost: (request: DownloadPostRequest): Promise<TaskResponse> =>
    api.post('/download-post', request).then(res => res.data),

  // Creator endpoints
  syncCreator: (request: SyncCreatorRequest): Promise<TaskResponse> =>
    api.post('/sync-creator', request).then(res => res.data),

  // Task management
  getTaskStatus: (taskId: string): Promise<TaskResponse> =>
    api.get(`/tasks/${taskId}`).then(res => res.data),

  getAllTasks: (): Promise<{ tasks: TaskResponse[] }> =>
    api.get('/tasks').then(res => res.data),

  deleteTask: (taskId: string): Promise<{ message: string }> =>
    api.delete(`/tasks/${taskId}`).then(res => res.data),
};

export default ktoolboxApi;