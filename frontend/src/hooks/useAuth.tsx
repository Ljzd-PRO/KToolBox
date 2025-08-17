import React, { createContext, useContext, useState, useEffect } from 'react'

interface AuthContextType {
  isAuthenticated: boolean
  username: string | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const credentials = localStorage.getItem('auth_credentials')
      if (!credentials) {
        setLoading(false)
        return
      }

      const response = await fetch('/auth/status', {
        headers: {
          'Authorization': `Basic ${credentials}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setIsAuthenticated(true)
        setUsername(data.username)
      } else {
        localStorage.removeItem('auth_credentials')
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('auth_credentials')
    } finally {
      setLoading(false)
    }
  }

  const login = async (usernameInput: string, password: string) => {
    try {
      const credentials = btoa(`${usernameInput}:${password}`)
      const response = await fetch('/auth/status', {
        headers: {
          'Authorization': `Basic ${credentials}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        localStorage.setItem('auth_credentials', credentials)
        setIsAuthenticated(true)
        setUsername(data.username)
        return true
      }
      return false
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  const logout = async () => {
    try {
      await fetch('/auth/logout', { method: 'POST' })
    } catch (error) {
      console.error('Logout request failed:', error)
    } finally {
      localStorage.removeItem('auth_credentials')
      setIsAuthenticated(false)
      setUsername(null)
    }
  }

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      username,
      login,
      logout,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}