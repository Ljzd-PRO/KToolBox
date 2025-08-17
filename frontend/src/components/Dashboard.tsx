import { Routes, Route, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { DownloadPost } from './features/DownloadPost'
import { SyncCreator } from './features/SyncCreator'
import { SearchCreator } from './features/SearchCreator'
import { Configuration } from './features/Configuration'
import { TaskManager } from './features/TaskManager'
import { InfoPanel } from './features/InfoPanel'

export function Dashboard() {
  const { username, logout } = useAuth()

  const navItems = [
    { path: '', label: 'Overview', component: InfoPanel },
    { path: 'download', label: 'Download Post', component: DownloadPost },
    { path: 'sync', label: 'Sync Creator', component: SyncCreator },
    { path: 'search', label: 'Search', component: SearchCreator },
    { path: 'tasks', label: 'Tasks', component: TaskManager },
    { path: 'config', label: 'Configuration', component: Configuration },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-2xl font-bold">KToolBox Web UI</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Welcome, {username}
            </span>
            <Button variant="outline" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Navigation Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Navigation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === ''}
                    className={({ isActive }) =>
                      `block px-3 py-2 rounded-md text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'hover:bg-accent hover:text-accent-foreground'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Routes>
              {navItems.map((item) => (
                <Route 
                  key={item.path}
                  path={item.path} 
                  element={<item.component />} 
                />
              ))}
            </Routes>
          </div>
        </div>
      </div>
    </div>
  )
}