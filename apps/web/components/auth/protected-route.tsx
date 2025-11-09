'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth/auth-context'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireRole?: 'admin' | 'manager' | 'user'
}

export function ProtectedRoute({ children, requireRole }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (!isLoading && user && requireRole) {
      const roleHierarchy: Record<string, number> = {
        user: 1,
        manager: 2,
        admin: 3,
      }

      const userRoleLevel = roleHierarchy[user.role] || 0
      const requiredRoleLevel = roleHierarchy[requireRole] || 0

      if (userRoleLevel < requiredRoleLevel) {
        router.push('/')
        return
      }
    }
  }, [isLoading, isAuthenticated, user, requireRole, router])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-indigo-600 mx-auto" />
          <p className="text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}

