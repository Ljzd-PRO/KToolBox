import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'

export function TaskManager() {
  const [tasks, setTasks] = useState<any>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 2000) // Refresh every 2 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchTasks = async () => {
    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) return

      const response = await fetch('/api/tasks', {
        headers: { 'Authorization': `Basic ${credentials}` }
      })

      if (response.ok) {
        const data = await response.json()
        setTasks(data.tasks)
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const cancelTask = async (taskId: string) => {
    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) return

      await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Basic ${credentials}` }
      })

      fetchTasks()
    } catch (error) {
      console.error('Failed to cancel task:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600'
      case 'running': return 'text-blue-600'
      case 'failed': return 'text-red-600'
      case 'cancelled': return 'text-gray-600'
      default: return 'text-yellow-600'
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">Loading tasks...</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Task Manager</CardTitle>
        <CardDescription>
          Monitor and manage download tasks
        </CardDescription>
      </CardHeader>
      <CardContent>
        {Object.keys(tasks).length === 0 ? (
          <div className="text-center text-muted-foreground">
            No tasks found
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(tasks).map(([taskId, task]: [string, any]) => (
              <div key={taskId} className="border rounded p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-mono text-sm text-muted-foreground">
                      {taskId}
                    </div>
                    <div className={`font-semibold ${getStatusColor(task.status)}`}>
                      Status: {task.status.toUpperCase()}
                    </div>
                    {task.progress !== undefined && (
                      <div className="text-sm text-muted-foreground">
                        Progress: {task.progress}%
                      </div>
                    )}
                    {task.error && (
                      <div className="text-sm text-red-600 mt-2">
                        Error: {task.error}
                      </div>
                    )}
                    {task.result && (
                      <div className="text-sm text-green-600 mt-2">
                        Completed successfully
                      </div>
                    )}
                  </div>
                  {task.status === 'running' && (
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => cancelTask(taskId)}
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}