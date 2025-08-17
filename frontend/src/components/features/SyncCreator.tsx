import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Button } from '../ui/button'

export function SyncCreator() {
  const [formData, setFormData] = useState({
    url: '',
    service: '',
    creator_id: '',
    path: '.',
    save_creator_indices: false,
    mix_posts: null,
    start_time: '',
    end_time: '',
    offset: 0,
    length: null,
    keywords: '',
    keywords_exclude: ''
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

      const response = await fetch('/api/sync/creator', {
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
        setResult({ error: 'Failed to start sync' })
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
        <CardTitle>Sync Creator</CardTitle>
        <CardDescription>
          Sync all posts from a creator
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
                placeholder="Creator URL"
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
              <label className="text-sm font-medium">Download Path</label>
              <Input
                value={formData.path}
                onChange={(e) => setFormData({...formData, path: e.target.value})}
                placeholder="."
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Start Time (YYYY-MM-DD)</label>
              <Input
                value={formData.start_time}
                onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                placeholder="2023-01-01"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">End Time (YYYY-MM-DD)</label>
              <Input
                value={formData.end_time}
                onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                placeholder="2023-12-31"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Keywords (comma separated)</label>
              <Input
                value={formData.keywords}
                onChange={(e) => setFormData({...formData, keywords: e.target.value})}
                placeholder="keyword1,keyword2"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Exclude Keywords</label>
              <Input
                value={formData.keywords_exclude}
                onChange={(e) => setFormData({...formData, keywords_exclude: e.target.value})}
                placeholder="exclude1,exclude2"
              />
            </div>
          </div>
          
          <Button type="submit" disabled={loading}>
            {loading ? 'Starting Sync...' : 'Sync Creator'}
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