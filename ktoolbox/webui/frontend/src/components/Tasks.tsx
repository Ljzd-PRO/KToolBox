import React, { useState, useEffect } from 'react';
import { ktoolboxApi } from '../utils/api';
import { TaskResponse } from '../types/api';

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null);

  const fetchTasks = async () => {
    try {
      const response = await ktoolboxApi.getAllTasks();
      setTasks(response.tasks);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  };

  const refreshTask = async (taskId: string) => {
    try {
      const updatedTask = await ktoolboxApi.getTaskStatus(taskId);
      setTasks(prev => prev.map(task => 
        task.task_id === taskId ? updatedTask : task
      ));
      if (selectedTask?.task_id === taskId) {
        setSelectedTask(updatedTask);
      }
    } catch (err) {
      console.error('Failed to refresh task:', err);
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      await ktoolboxApi.deleteTask(taskId);
      setTasks(prev => prev.filter(task => task.task_id !== taskId));
      if (selectedTask?.task_id === taskId) {
        setSelectedTask(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete task');
    }
  };

  useEffect(() => {
    fetchTasks();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'running': return 'text-blue-600';
      case 'failed': return 'text-red-600';
      default: return 'text-yellow-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'failed': return '❌';
      default: return '⏳';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-b-2 border-primary rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tasks</h1>
          <p className="text-muted-foreground mt-2">
            Monitor and manage running tasks
          </p>
        </div>
        <button
          onClick={fetchTasks}
          className="btn btn-outline px-4 py-2"
        >
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task List */}
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">All Tasks ({tasks.length})</h2>
          
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <div className="text-4xl mb-2">📭</div>
              <p>No tasks found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.task_id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedTask?.task_id === task.task_id 
                      ? 'border-primary bg-primary/5' 
                      : 'hover:bg-accent'
                  }`}
                  onClick={() => setSelectedTask(task)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{getStatusIcon(task.status)}</span>
                      <div>
                        <div className="font-medium">Task {task.task_id.slice(0, 8)}...</div>
                        <div className="text-sm text-muted-foreground">
                          Type: {(task as any).type || 'Unknown'}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium capitalize ${getStatusColor(task.status)}`}>
                        {task.status}
                      </div>
                      <div className="flex gap-2 mt-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            refreshTask(task.task_id);
                          }}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          Refresh
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteTask(task.task_id);
                          }}
                          className="text-sm text-red-600 hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Task Details */}
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">Task Details</h2>
          
          {selectedTask ? (
            <div className="space-y-4">
              <div>
                <label className="label">Task ID</label>
                <div className="font-mono text-sm bg-muted p-2 rounded">
                  {selectedTask.task_id}
                </div>
              </div>

              <div>
                <label className="label">Status</label>
                <div className={`font-medium capitalize ${getStatusColor(selectedTask.status)}`}>
                  {getStatusIcon(selectedTask.status)} {selectedTask.status}
                </div>
              </div>

              {selectedTask.error && (
                <div>
                  <label className="label">Error</label>
                  <div className="text-red-600 bg-red-50 p-3 rounded border border-red-200">
                    {selectedTask.error}
                  </div>
                </div>
              )}

              {selectedTask.result && (
                <div>
                  <label className="label">Result</label>
                  <div className="bg-muted p-3 rounded overflow-auto max-h-64">
                    <pre className="text-sm">
                      {typeof selectedTask.result === 'string' 
                        ? selectedTask.result 
                        : JSON.stringify(selectedTask.result, null, 2)
                      }
                    </pre>
                  </div>
                </div>
              )}

              {selectedTask.progress && (
                <div>
                  <label className="label">Progress</label>
                  <div className="bg-muted p-3 rounded">
                    <pre className="text-sm">
                      {JSON.stringify(selectedTask.progress, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => refreshTask(selectedTask.task_id)}
                  className="btn btn-outline px-4 py-2"
                >
                  🔄 Refresh
                </button>
                <button
                  onClick={() => deleteTask(selectedTask.task_id)}
                  className="btn btn-outline px-4 py-2 text-red-600 border-red-200 hover:bg-red-50"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <div className="text-4xl mb-2">👆</div>
              <p>Select a task to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};