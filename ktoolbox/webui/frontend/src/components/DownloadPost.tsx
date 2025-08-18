import React, { useState } from 'react';
import { ktoolboxApi } from '../utils/api';
import { TaskResponse } from '../types/api';

export const DownloadPost: React.FC = () => {
  const [formData, setFormData] = useState({
    url: '',
    service: '',
    creator_id: '',
    post_id: '',
    revision_id: '',
    path: '.',
    dump_post_data: true,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [useUrl, setUseUrl] = useState(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const request = useUrl
        ? {
            url: formData.url,
            path: formData.path,
            dump_post_data: formData.dump_post_data,
          }
        : {
            service: formData.service,
            creator_id: formData.creator_id,
            post_id: formData.post_id,
            revision_id: formData.revision_id || undefined,
            path: formData.path,
            dump_post_data: formData.dump_post_data,
          };

      const response = await ktoolboxApi.downloadPost(request);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Download Post</h1>
        <p className="text-muted-foreground mt-2">
          Download a specific post or revision from Kemono
        </p>
      </div>

      <div className="card p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Input Method Toggle */}
          <div className="space-y-3">
            <label className="label">Input Method</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={useUrl}
                  onChange={() => setUseUrl(true)}
                  className="h-4 w-4"
                />
                <span>URL</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={!useUrl}
                  onChange={() => setUseUrl(false)}
                  className="h-4 w-4"
                />
                <span>Service Details</span>
              </label>
            </div>
          </div>

          {useUrl ? (
            <div className="space-y-3">
              <label htmlFor="url" className="label">
                Post URL *
              </label>
              <input
                type="url"
                id="url"
                name="url"
                value={formData.url}
                onChange={handleInputChange}
                placeholder="https://kemono.su/fanbox/user/49494721/post/6608808"
                className="input"
                required
              />
              <p className="text-sm text-muted-foreground">
                Enter the full URL to the post you want to download
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <label htmlFor="service" className="label">
                  Service *
                </label>
                <select
                  id="service"
                  name="service"
                  value={formData.service}
                  onChange={handleInputChange}
                  className="select"
                  required
                >
                  <option value="">Select Service</option>
                  <option value="fanbox">Fanbox</option>
                  <option value="patreon">Patreon</option>
                  <option value="gumroad">Gumroad</option>
                  <option value="subscribestar">SubscribeStar</option>
                  <option value="dlsite">DLsite</option>
                  <option value="fantia">Fantia</option>
                </select>
              </div>

              <div className="space-y-3">
                <label htmlFor="creator_id" className="label">
                  Creator ID *
                </label>
                <input
                  type="text"
                  id="creator_id"
                  name="creator_id"
                  value={formData.creator_id}
                  onChange={handleInputChange}
                  placeholder="49494721"
                  className="input"
                  required
                />
              </div>

              <div className="space-y-3">
                <label htmlFor="post_id" className="label">
                  Post ID *
                </label>
                <input
                  type="text"
                  id="post_id"
                  name="post_id"
                  value={formData.post_id}
                  onChange={handleInputChange}
                  placeholder="6608808"
                  className="input"
                  required
                />
              </div>

              <div className="space-y-3">
                <label htmlFor="revision_id" className="label">
                  Revision ID (Optional)
                </label>
                <input
                  type="text"
                  id="revision_id"
                  name="revision_id"
                  value={formData.revision_id}
                  onChange={handleInputChange}
                  placeholder="Leave empty for latest"
                  className="input"
                />
              </div>
            </div>
          )}

          {/* Common Options */}
          <div className="space-y-3">
            <label htmlFor="path" className="label">
              Download Path
            </label>
            <input
              type="text"
              id="path"
              name="path"
              value={formData.path}
              onChange={handleInputChange}
              placeholder="."
              className="input"
            />
            <p className="text-sm text-muted-foreground">
              Directory where files will be saved (default: current directory)
            </p>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="dump_post_data"
              name="dump_post_data"
              checked={formData.dump_post_data}
              onChange={handleInputChange}
              className="h-4 w-4"
            />
            <label htmlFor="dump_post_data" className="label">
              Save post metadata
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`btn btn-primary px-6 py-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin h-4 w-4 border-b-2 border-white rounded-full"></div>
                Starting Download...
              </div>
            ) : (
              'Download Post'
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-3">Task Started</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Task ID:</span>
              <span className="font-mono text-sm">{result.task_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Status:</span>
              <span className={`font-medium capitalize ${
                result.status === 'pending' ? 'text-yellow-600' :
                result.status === 'running' ? 'text-blue-600' :
                result.status === 'completed' ? 'text-green-600' : 'text-red-600'
              }`}>
                {result.status}
              </span>
            </div>
          </div>
          <div className="mt-4">
            <a
              href="/tasks"
              className="btn btn-outline px-4 py-2"
            >
              View in Tasks
            </a>
          </div>
        </div>
      )}
    </div>
  );
};