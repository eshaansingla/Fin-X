import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api, setAuthToken } from '../api'

const AuthContext = createContext(null)
const TOKEN_KEY = 'finx_token'

export function useAuth() {
  return useContext(AuthContext)
}

export default function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || null)
  const [user, setUser] = useState(null)

  useEffect(() => {
    setAuthToken(token)
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }, [token])

  const refreshMe = async () => {
    try {
      const me = await api.get('/auth/me')
      setUser(me)
    } catch {
      setToken(null)
      setUser(null)
    }
  }

  // Restore user info on mount if a saved token exists
  useEffect(() => {
    if (token) refreshMe()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const value = useMemo(() => {
    const isAuthed = !!token

    const login = async ({ email, password }) => {
      const res = await api.post('/auth/login', { email, password })
      const finalToken = res?.access_token || res?.accessToken || res?.token
      if (!finalToken) throw new Error('Login succeeded but no token returned')
      setToken(finalToken)
      return true
    }

    const register = async ({ email, password }) => {
      return await api.post('/auth/register', { email, password })
    }

    const logout = () => {
      setToken(null)
      setUser(null)
    }

    return { token, user, isAuthed, login, register, logout, refreshMe }
  }, [token, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

