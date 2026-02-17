import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/router'
import Cookies from 'js-cookie'
import { authAPI } from '@/lib/api'

interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  is_active: boolean
  role: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const token = Cookies.get('auth_token')
    if (token) {
      authAPI
        .me()
        .then((res: any) => setUser(res.data))
        .catch(() => {
          Cookies.remove('auth_token')
          Cookies.remove('refresh_token')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authAPI.login({ email, password })
    const { access_token, refresh_token } = response.data
    Cookies.set('auth_token', access_token, { expires: 1, sameSite: 'Lax' })
    Cookies.set('refresh_token', refresh_token, { expires: 7, sameSite: 'Lax' })
    const meRes = await authAPI.me()
    setUser(meRes.data)
  }

  const logout = () => {
    Cookies.remove('auth_token')
    Cookies.remove('refresh_token')
    setUser(null)
    router.push('/auth/login')
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, logout, isAuthenticated: !!user }}
    >
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
