import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api } from '../api/client'
import { clearToken, getToken, setToken } from '../utils/storage'
import type { UserResponse } from '../types/api'

interface AuthContextValue {
  user: UserResponse | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: {
    email: string
    password: string
    full_name?: string
    org_name: string
    org_slug: string
  }) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [token, setTokenState] = useState<string | null>(getToken())
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const currentToken = getToken()
    if (!currentToken) {
      setUser(null)
      setTokenState(null)
      return
    }
    const me = await api.me(currentToken)
    setUser(me)
    setTokenState(currentToken)
  }, [])

  useEffect(() => {
    refreshUser()
      .catch(() => {
        clearToken()
        setUser(null)
        setTokenState(null)
      })
      .finally(() => setLoading(false))
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login({ email, password })
    setToken(access_token)
    setTokenState(access_token)
    const me = await api.me(access_token)
    setUser(me)
  }, [])

  const register = useCallback(
    async (data: {
      email: string
      password: string
      full_name?: string
      org_name: string
      org_slug: string
    }) => {
      const { access_token } = await api.register(data)
      setToken(access_token)
      setTokenState(access_token)
      const me = await api.me(access_token)
      setUser(me)
    },
    [],
  )

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    setTokenState(null)
  }, [])

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout, refreshUser }),
    [user, token, loading, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
