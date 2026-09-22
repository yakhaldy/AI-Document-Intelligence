import { useCallback, useEffect, useMemo, useState } from 'react'
import { getMe, login as apiLogin } from '../api'
import { AuthContext } from './auth-context'

const STORAGE_KEY = 'adi_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState(null)

  const login = useCallback(async (username, password) => {
    const { access_token } = await apiLogin(username, password)
    localStorage.setItem(STORAGE_KEY, access_token)
    setToken(access_token)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    if (!token) return

    let cancelled = false
    async function fetchUser() {
      try {
        const me = await getMe(token)
        if (!cancelled) setUser(me)
      } catch {
        if (!cancelled) logout()
      }
    }

    fetchUser()
    return () => {
      cancelled = true
    }
  }, [token, logout])

  const value = useMemo(
    () => ({ token, user, isAdmin: user?.role === 'admin', isAuthenticated: !!token, login, logout }),
    [token, user, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
