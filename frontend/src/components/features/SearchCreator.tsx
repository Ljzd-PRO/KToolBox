import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Button } from '../ui/button'

export function SearchCreator() {
  const [creatorForm, setCreatorForm] = useState({
    name: '',
    id: '',
    service: ''
  })
  const [postForm, setPostForm] = useState({
    id: '',
    name: '',
    service: '',
    q: '',
    o: 0
  })
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)

  const searchCreators = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResults(null)

    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) return

      const response = await fetch('/api/search/creator', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${credentials}`
        },
        body: JSON.stringify(creatorForm)
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
      } else {
        setResults({ error: 'Search failed' })
      }
    } catch (error) {
      setResults({ error: 'Network error' })
    } finally {
      setLoading(false)
    }
  }

  const searchPosts = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResults(null)

    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) return

      const response = await fetch('/api/search/creator-posts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${credentials}`
        },
        body: JSON.stringify(postForm)
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
      } else {
        setResults({ error: 'Search failed' })
      }
    } catch (error) {
      setResults({ error: 'Network error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Search Creators</CardTitle>
          <CardDescription>
            Search for creators by name, ID, or service
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={searchCreators} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={creatorForm.name}
                  onChange={(e) => setCreatorForm({...creatorForm, name: e.target.value})}
                  placeholder="Creator name"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">ID</label>
                <Input
                  value={creatorForm.id}
                  onChange={(e) => setCreatorForm({...creatorForm, id: e.target.value})}
                  placeholder="Creator ID"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Service</label>
                <Input
                  value={creatorForm.service}
                  onChange={(e) => setCreatorForm({...creatorForm, service: e.target.value})}
                  placeholder="e.g., patreon"
                />
              </div>
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Search Creators'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Search Creator Posts</CardTitle>
          <CardDescription>
            Search posts from a specific creator
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={searchPosts} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Creator ID</label>
                <Input
                  value={postForm.id}
                  onChange={(e) => setPostForm({...postForm, id: e.target.value})}
                  placeholder="Creator ID"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Creator Name</label>
                <Input
                  value={postForm.name}
                  onChange={(e) => setPostForm({...postForm, name: e.target.value})}
                  placeholder="Creator name"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Service</label>
                <Input
                  value={postForm.service}
                  onChange={(e) => setPostForm({...postForm, service: e.target.value})}
                  placeholder="e.g., patreon"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Search Query</label>
                <Input
                  value={postForm.q}
                  onChange={(e) => setPostForm({...postForm, q: e.target.value})}
                  placeholder="Search query"
                />
              </div>
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Search Posts'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {results && (
        <Card>
          <CardHeader>
            <CardTitle>Search Results</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm overflow-auto max-h-96">
              {JSON.stringify(results, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}