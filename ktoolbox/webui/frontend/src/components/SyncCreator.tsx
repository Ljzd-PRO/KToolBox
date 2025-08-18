import React, { useState } from 'react';
import { ktoolboxApi } from '../utils/api';
import { TaskResponse } from '../types/api';

export const SyncCreator: React.FC = () => {
  const [formData, setFormData] = useState({
    url: '',
    service: '',
    creator_id: '',
    path: '.',
    save_creator_indices: false,
    mix_posts: false,
    start_time: '',
    end_time: '',
    offset: 0,
    length: '',
    keywords: '',
    keywords_exclude: '',
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
      const request = {
        ...(useUrl ? { url: formData.url } : { service: formData.service, creator_id: formData.creator_id }),
        path: formData.path,
        save_creator_indices: formData.save_creator_indices,
        mix_posts: formData.mix_posts || undefined,
        start_time: formData.start_time || undefined,
        end_time: formData.end_time || undefined,
        offset: formData.offset,
        length: formData.length ? parseInt(formData.length) : undefined,
        keywords: formData.keywords || undefined,
        keywords_exclude: formData.keywords_exclude || undefined,
      };

      const response = await ktoolboxApi.syncCreator(request);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Sync Creator</h1>
        <p className="text-muted-foreground mt-2">
          Sync all posts from a creator. You can update the directory anytime after download finished.
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
                <span>Creator URL</span>
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
                Creator URL *
              </label>
              <input
                type="url"
                id="url"
                name="url"
                value={formData.url}
                onChange={handleInputChange}
                placeholder="https://kemono.su/fanbox/user/49494721"
                className="input"
                required
              />
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
            </div>
          )}

          {/* Download Options */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Download Options</h3>
            
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
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <label htmlFor="offset" className="label">
                  Offset
                </label>
                <input
                  type="number"
                  id="offset"
                  name="offset"
                  value={formData.offset}
                  onChange={handleInputChange}
                  min="0"
                  className="input"
                />
              </div>

              <div className="space-y-3">
                <label htmlFor="length" className="label">
                  Number of Posts (Optional)
                </label>
                <input
                  type="number"
                  id="length"
                  name="length"
                  value={formData.length}
                  onChange={handleInputChange}
                  min="1"
                  placeholder="All posts"
                  className="input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <label htmlFor="start_time" className="label">
                  Start Date (Optional)
                </label>
                <input
                  type="date"
                  id="start_time"
                  name="start_time"
                  value={formData.start_time}
                  onChange={handleInputChange}
                  className="input"
                />
              </div>

              <div className="space-y-3">
                <label htmlFor="end_time" className="label">
                  End Date (Optional)
                </label>
                <input
                  type="date"
                  id="end_time"
                  name="end_time"
                  value={formData.end_time}
                  onChange={handleInputChange}
                  className="input"
                />
              </div>
            </div>

            <div className="space-y-3">
              <label htmlFor="keywords" className="label">
                Keywords (Optional)
              </label>
              <input
                type="text"
                id="keywords"
                name="keywords"
                value={formData.keywords}
                onChange={handleInputChange}
                placeholder="keyword1,keyword2,keyword3"
                className="input"
              />
              <p className="text-sm text-muted-foreground">Comma-separated keywords to filter posts by title</p>
            </div>

            <div className="space-y-3">
              <label htmlFor="keywords_exclude" className="label">
                Exclude Keywords (Optional)
              </label>
              <input
                type="text"
                id="keywords_exclude"
                name="keywords_exclude"
                value={formData.keywords_exclude}
                onChange={handleInputChange}
                placeholder="exclude1,exclude2,exclude3"
                className="input"
              />
              <p className="text-sm text-muted-foreground">Comma-separated keywords to exclude posts by title</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="save_creator_indices"
                  name="save_creator_indices"
                  checked={formData.save_creator_indices}
                  onChange={handleInputChange}
                  className="h-4 w-4"
                />
                <label htmlFor="save_creator_indices" className="label">
                  Save creator indices data
                </label>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="mix_posts"
                  name="mix_posts"
                  checked={formData.mix_posts}
                  onChange={handleInputChange}
                  className="h-4 w-4"
                />
                <label htmlFor="mix_posts" className="label">
                  Mix posts (save all files from different posts at same path)
                </label>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`btn btn-primary px-6 py-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin h-4 w-4 border-b-2 border-white rounded-full"></div>
                Starting Sync...
              </div>
            ) : (
              'Start Sync'
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