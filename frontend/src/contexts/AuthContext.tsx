import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'

interface User {
  id: number
  email: string
  name: string
  avatar_url: string | null
}

interface AuthContextType {
  user: User | null
  loading: boolean
  devLoginEnabled: boolean
  login: (email: string) => Promise<void>
  loginWithGoogle: () => void
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [devLoginEnabled, setDevLoginEnabled] = useState(false)

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch('/api/auth/status', { credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        setUser(data.user)
        setDevLoginEnabled(data.dev_login_enabled)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = useCallback(async (email: string) => {
    const res = await fetch('/api/auth/dev-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email }),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(error.detail || 'Login failed')
    }
    const userData = await res.json()
    setUser(userData)
  }, [])

  const loginWithGoogle = useCallback(() => {
    window.location.href = '/api/auth/login'
  }, [])

  const logout = useCallback(async () => {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })
    setUser(null)
  }, [])

  const refreshAuth = useCallback(async () => {
    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      })
      if (res.ok) {
        const userData = await res.json()
        setUser(userData)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{ user, loading, devLoginEnabled, login, loginWithGoogle, logout, refreshAuth }}
    >
      {children}
    </AuthContext.Provider>
  )
}
