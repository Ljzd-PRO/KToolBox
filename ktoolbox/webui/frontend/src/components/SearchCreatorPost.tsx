import React, { useState } from 'react';
import { ktoolboxApi } from '../utils/api';
import { TaskResponse } from '../types/api';

export const SearchCreatorPost: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    id: '',
    service: '',
    q: '',
    o: '',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const request = {
        name: formData.name || undefined,
        id: formData.id || undefined,
        service: formData.service || undefined,
        q: formData.q || undefined,
        o: formData.o ? parseInt(formData.o) : undefined,
      };

      const response = await ktoolboxApi.searchCreatorPost(request);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Search Creator Posts</h1>
        <p className="text-muted-foreground mt-2">
          Search for posts from a specific creator. You can use multiple parameters as keywords.
        </p>
      </div>

      <div className="card p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-3">
              <label htmlFor="name" className="label">
                Creator Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Artist name"
                className="input"
              />
            </div>

            <div className="space-y-3">
              <label htmlFor="id" className="label">
                Creator ID
              </label>
              <input
                type="text"
                id="id"
                name="id"
                value={formData.id}
                onChange={handleInputChange}
                placeholder="49494721"
                className="input"
              />
            </div>

            <div className="space-y-3">
              <label htmlFor="service" className="label">
                Service
              </label>
              <select
                id="service"
                name="service"
                value={formData.service}
                onChange={handleInputChange}
                className="select"
              >
                <option value="">All Services</option>
                <option value="fanbox">Fanbox</option>
                <option value="patreon">Patreon</option>
                <option value="gumroad">Gumroad</option>
                <option value="subscribestar">SubscribeStar</option>
                <option value="dlsite">DLsite</option>
                <option value="fantia">Fantia</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <label htmlFor="q" className="label">
                Search Query
              </label>
              <input
                type="text"
                id="q"
                name="q"
                value={formData.q}
                onChange={handleInputChange}
                placeholder="Search terms..."
                className="input"
              />
              <p className="text-sm text-muted-foreground">
                Search within post titles and descriptions
              </p>
            </div>

            <div className="space-y-3">
              <label htmlFor="o" className="label">
                Offset
              </label>
              <input
                type="number"
                id="o"
                name="o"
                value={formData.o}
                onChange={handleInputChange}
                placeholder="0"
                min="0"
                step="50"
                className="input"
              />
              <p className="text-sm text-muted-foreground">
                Result offset, stepping of 50 is enforced
              </p>
            </div>
          </div>

          <div className="alert alert-info">
            <strong>Note:</strong> You need to provide at least one of: creator name, ID, or service to search for posts.
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`btn btn-primary px-6 py-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin h-4 w-4 border-b-2 border-white rounded-full"></div>
                Searching...
              </div>
            ) : (
              'Search Posts'
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
          <h3 className="text-lg font-semibold mb-3">Search Started</h3>
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
              View Results in Tasks
            </a>
          </div>
        </div>
      )}
    </div>
  );
};