import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'

export function Configuration() {
  const [config, setConfig] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) return

      const response = await fetch('/api/config', {
        headers: { 'Authorization': `Basic ${credentials}` }
      })

      if (response.ok) {
        const data = await response.json()
        setConfig(data)
      } else {
        setError('Failed to fetch configuration')
      }
    } catch (err) {
      setError('Failed to fetch configuration')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">Loading configuration...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-destructive">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Configuration Overview</CardTitle>
          <CardDescription>
            Current KToolBox configuration settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">API Configuration</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                <div>Scheme: {config?.api?.scheme}</div>
                <div>Netloc: {config?.api?.netloc}</div>
                <div>Timeout: {config?.api?.timeout}s</div>
                <div>Retry times: {config?.api?.retry_times}</div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Downloader Configuration</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                <div>Pool size: {config?.downloader?.pool_size}</div>
                <div>Retries: {config?.downloader?.retries}</div>
                <div>Chunk size: {config?.downloader?.chunk_size} bytes</div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Job Configuration</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                <div>Allow list: {config?.job?.allow_list?.join(', ') || 'None'}</div>
                <div>Block list: {config?.job?.block_list?.join(', ') || 'None'}</div>
                <div>Group by year: {config?.job?.group_by_year ? 'Yes' : 'No'}</div>
                <div>Group by month: {config?.job?.group_by_month ? 'Yes' : 'No'}</div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Web UI Configuration</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                <div>Host: {config?.webui?.host}</div>
                <div>Port: {config?.webui?.port}</div>
                <div>Debug mode: {config?.webui?.debug ? 'Enabled' : 'Disabled'}</div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">General Settings</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                <div>SSL verify: {config?.ssl_verify ? 'Enabled' : 'Disabled'}</div>
                <div>JSON dump indent: {config?.json_dump_indent}</div>
                <div>Use uvloop: {config?.use_uvloop ? 'Enabled' : 'Disabled'}</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Raw Configuration</CardTitle>
          <CardDescription>
            Complete configuration in JSON format
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="text-xs overflow-auto max-h-96 bg-muted p-4 rounded">
            {JSON.stringify(config, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}