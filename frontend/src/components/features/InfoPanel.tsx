import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'

interface VersionInfo {
  version: string
  site_version: string
}

export function InfoPanel() {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchVersionInfo()
  }, [])

  const fetchVersionInfo = async () => {
    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) return

      const [versionRes, siteVersionRes] = await Promise.all([
        fetch('/api/version', {
          headers: { 'Authorization': `Basic ${credentials}` }
        }),
        fetch('/api/site-version', {
          headers: { 'Authorization': `Basic ${credentials}` }
        })
      ])

      if (versionRes.ok && siteVersionRes.ok) {
        const version = await versionRes.json()
        const siteVersion = await siteVersionRes.json()
        
        setVersionInfo({
          version: version.version,
          site_version: siteVersion.site_version
        })
      } else {
        setError('Failed to fetch version information')
      }
    } catch (err) {
      setError('Failed to fetch version information')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">Loading...</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Welcome to KToolBox Web UI</CardTitle>
          <CardDescription>
            Web interface for KToolBox - Kemono content downloader
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">Available Features:</h3>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Download individual posts or revisions</li>
                <li>• Sync all posts from a creator</li>
                <li>• Search for creators and posts</li>
                <li>• Monitor download tasks in real-time</li>
                <li>• Manage configuration settings</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {error ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      ) : versionInfo && (
        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold text-sm mb-1">KToolBox Version</h4>
                <p className="text-sm text-muted-foreground">{versionInfo.version}</p>
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-1">Site Version</h4>
                <p className="text-sm text-muted-foreground">{versionInfo.site_version}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}