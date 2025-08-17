import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Button } from '../ui/button'

export function DownloadPost() {
  const [formData, setFormData] = useState({
    url: '',
    service: '',
    creator_id: '',
    post_id: '',
    revision_id: '',
    path: '.',
    dump_post_data: true
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) return

      const response = await fetch('/api/download/post', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${credentials}`
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        const data = await response.json()
        setResult(data)
      } else {
        setResult({ error: 'Failed to start download' })
      }
    } catch (error) {
      setResult({ error: 'Network error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Download Post</CardTitle>
        <CardDescription>
          Download a specific post or revision
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">URL</label>
              <Input
                value={formData.url}
                onChange={(e) => setFormData({...formData, url: e.target.value})}
                placeholder="Post URL"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Service</label>
              <Input
                value={formData.service}
                onChange={(e) => setFormData({...formData, service: e.target.value})}
                placeholder="e.g., patreon"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Creator ID</label>
              <Input
                value={formData.creator_id}
                onChange={(e) => setFormData({...formData, creator_id: e.target.value})}
                placeholder="Creator ID"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Post ID</label>
              <Input
                value={formData.post_id}
                onChange={(e) => setFormData({...formData, post_id: e.target.value})}
                placeholder="Post ID"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Revision ID (Optional)</label>
              <Input
                value={formData.revision_id}
                onChange={(e) => setFormData({...formData, revision_id: e.target.value})}
                placeholder="Revision ID"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Download Path</label>
              <Input
                value={formData.path}
                onChange={(e) => setFormData({...formData, path: e.target.value})}
                placeholder="."
              />
            </div>
          </div>
          
          <Button type="submit" disabled={loading}>
            {loading ? 'Starting Download...' : 'Download Post'}
          </Button>
        </form>

        {result && (
          <div className="mt-4 p-4 border rounded">
            <pre className="text-sm">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </CardContent>
    </Card>
  )
}