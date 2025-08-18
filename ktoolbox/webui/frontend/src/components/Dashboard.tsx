import React, { useState, useEffect } from 'react';
import { ktoolboxApi } from '../utils/api';

export const Dashboard: React.FC = () => {
  const [version, setVersion] = useState<string>('');
  const [siteVersion, setSiteVersion] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [versionRes, siteVersionRes, tasksRes] = await Promise.all([
          ktoolboxApi.getVersion(),
          ktoolboxApi.getSiteVersion(),
          ktoolboxApi.getAllTasks(),
        ]);
        
        setVersion(versionRes.version);
        setSiteVersion(siteVersionRes.site_version);
        setTasks(tasksRes.tasks);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-b-2 border-primary rounded-full"></div>
      </div>
    );
  }

  const completedTasks = tasks.filter(task => task.status === 'completed');
  const runningTasks = tasks.filter(task => task.status === 'running');
  const failedTasks = tasks.filter(task => task.status === 'failed');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome to KToolBox WebUI - A web interface for downloading posts from Kemono.cr / .su / .party
        </p>
      </div>

      {/* Version Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="text-2xl">📦</div>
            <div>
              <h3 className="font-semibold">KToolBox Version</h3>
              <p className="text-2xl font-bold text-primary">{version}</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="text-2xl">🌐</div>
            <div>
              <h3 className="font-semibold">Site Version</h3>
              <p className="text-lg font-medium text-muted-foreground">{siteVersion}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Task Statistics */}
      <div className="card p-6">
        <h3 className="text-xl font-semibold mb-4">Task Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{tasks.length}</div>
            <div className="text-sm text-muted-foreground">Total Tasks</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">{runningTasks.length}</div>
            <div className="text-sm text-muted-foreground">Running</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{completedTasks.length}</div>
            <div className="text-sm text-muted-foreground">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{failedTasks.length}</div>
            <div className="text-sm text-muted-foreground">Failed</div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <a 
            href="/download-post" 
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">⬇️</div>
            <div>
              <div className="font-medium">Download Post</div>
              <div className="text-sm text-muted-foreground">Download a specific post</div>
            </div>
          </a>

          <a 
            href="/sync-creator" 
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">🔄</div>
            <div>
              <div className="font-medium">Sync Creator</div>
              <div className="text-sm text-muted-foreground">Sync all posts from a creator</div>
            </div>
          </a>

          <a 
            href="/search-creator" 
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">👤</div>
            <div>
              <div className="font-medium">Search Creator</div>
              <div className="text-sm text-muted-foreground">Find creators by name or ID</div>
            </div>
          </a>

          <a 
            href="/search-creator-post" 
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">🔍</div>
            <div>
              <div className="font-medium">Search Posts</div>
              <div className="text-sm text-muted-foreground">Search posts from creators</div>
            </div>
          </a>

          <a 
            href="/tasks" 
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">📋</div>
            <div>
              <div className="font-medium">View Tasks</div>
              <div className="text-sm text-muted-foreground">Monitor running tasks</div>
            </div>
          </a>

          <a 
            href="/settings" 
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">⚙️</div>
            <div>
              <div className="font-medium">Settings</div>
              <div className="text-sm text-muted-foreground">Configure KToolBox</div>
            </div>
          </a>
        </div>
      </div>

      {/* Recent Tasks */}
      {tasks.length > 0 && (
        <div className="card p-6">
          <h3 className="text-xl font-semibold mb-4">Recent Tasks</h3>
          <div className="space-y-2">
            {tasks.slice(0, 5).map((task) => (
              <div key={task.id} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    task.status === 'completed' ? 'bg-green-500' :
                    task.status === 'running' ? 'bg-yellow-500' :
                    task.status === 'failed' ? 'bg-red-500' : 'bg-gray-500'
                  }`}></div>
                  <div>
                    <div className="font-medium">{task.type}</div>
                    <div className="text-sm text-muted-foreground">{task.id}</div>
                  </div>
                </div>
                <div className="text-sm font-medium capitalize">{task.status}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};