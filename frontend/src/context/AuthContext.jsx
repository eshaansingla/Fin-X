import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api, setAuthToken } from '../api'

const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}

export default function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)

  useEffect(() => {
    setAuthToken(token)
  }, [token])

  const refreshMe = async () => {
    try {
      const me = await api.get('/auth/me')
      setUser(me)
    } catch {
      // Token might be expired; clear it.
      setToken(null)
      setUser(null)
    }
  }

  const value = useMemo(() => {
    const isAuthed = !!token

    const login = async ({ email, password }) => {
      const res = await api.post('/auth/login', { email, password })
      // `api` unwrap returns `body.data` for `{success:true}` responses, so `res` is that data.
      const finalToken = res?.access_token || res?.accessToken || res?.token
      if (!finalToken) throw new Error('Login succeeded but no token returned')
      setToken(finalToken)
      await refreshMe()
      return true
    }

    const register = async ({ email, password }) => {
      await api.post('/auth/register', { email, password })
      return login({ email, password })
    }

    const logout = () => {
      setToken(null)
      setUser(null)
    }

    return { token, user, isAuthed, login, register, logout, refreshMe }
  }, [token, user])

  useEffect(() => {
    if (token) refreshMe()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

