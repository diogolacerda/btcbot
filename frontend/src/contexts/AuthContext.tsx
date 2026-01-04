import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import type { User } from '@/types'
import type { LoginRequest, RegisterRequest } from '@/types/api'
import * as authService from '@/services/auth'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Auto-fetch user on mount if token exists
  useEffect(() => {
    const initializeAuth = async () => {
      // Check if we have a token
      if (!authService.hasToken()) {
        setIsLoading(false)
        return
      }

      // Try to get cached user first for instant UI
      const cachedUser = authService.getCachedUser()
      if (cachedUser) {
        setUser(cachedUser)
      }

      // Then fetch fresh user data from API
      try {
        const freshUser = await authService.getCurrentUser()
        setUser(freshUser)

        // Update cache
        localStorage.setItem('user', JSON.stringify(freshUser))
      } catch (error) {
        console.error('Failed to fetch user on mount:', error)

        // Token might be expired or invalid
        authService.logout()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true)
    try {
      const user = await authService.login(credentials)
      setUser(user)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (userData: RegisterRequest) => {
    setIsLoading(true)
    try {
      const user = await authService.register(userData)
      setUser(user)
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  const refreshUser = async () => {
    if (!authService.hasToken()) {
      return
    }

    try {
      const freshUser = await authService.getCurrentUser()
      setUser(freshUser)

      // Update cache
      localStorage.setItem('user', JSON.stringify(freshUser))
    } catch (error) {
      console.error('Failed to refresh user:', error)

      // Token might be expired
      logout()
      throw error
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Hook to use auth context
 * Throws error if used outside of AuthProvider
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
