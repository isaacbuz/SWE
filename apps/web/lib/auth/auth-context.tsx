'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api/client'

export interface User {
  id: number
  user_id: string
  username: string
  email: string
  display_name?: string
  role: 'admin' | 'manager' | 'user' | 'service'
  is_active: boolean
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // Check for existing session on mount
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
      if (!token) {
        setIsLoading(false)
        return
      }

      // Verify token and get user
      const userData = await api.get<User>('/auth/me')
      setUser(userData)
    } catch (error) {
      // Token invalid or expired
      localStorage.removeItem('auth_token')
      sessionStorage.removeItem('auth_token')
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    try {
      const response = await api.post<{ access_token: string; token_type: string; user: User }>('/auth/login', {
        email,
        password,
      })

      // Store token
      localStorage.setItem('auth_token', response.access_token)
      setUser(response.user)
      router.push('/')
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(error.message)
      }
      throw new Error('Login failed')
    }
  }, [router])

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token')
    sessionStorage.removeItem('auth_token')
    setUser(null)
    router.push('/login')
  }, [router])

  const refreshUser = useCallback(async () => {
    try {
      const userData = await api.get<User>('/auth/me')
      setUser(userData)
    } catch (error) {
      logout()
    }
  }, [logout])

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
      }}
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

