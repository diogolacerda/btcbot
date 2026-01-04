import { axiosInstance } from '@/lib/axios'
import { transformKeysToCamel, transformKeysToSnake } from '@/lib/transformers'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse
} from '@/types/api'
import type { User } from '@/types'

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user'

/**
 * Login with email and password
 * Uses form-data format (application/x-www-form-urlencoded)
 * Backend expects 'email' and 'password' fields
 */
export async function login(credentials: LoginRequest): Promise<User> {
  // Convert to form data
  const formData = new URLSearchParams()
  formData.append('email', credentials.email)
  formData.append('password', credentials.password)

  const response = await axiosInstance.post<TokenResponse>(
    '/v1/auth/login',
    formData,
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    }
  )

  // Transform response from snake_case to camelCase
  const tokenData = transformKeysToCamel<TokenResponse>(response.data)

  // Store token in localStorage
  localStorage.setItem(TOKEN_KEY, tokenData.accessToken)

  // Fetch and return user data
  const user = await getCurrentUser()

  // Cache user in localStorage
  localStorage.setItem(USER_KEY, JSON.stringify(user))

  return user
}

/**
 * Register a new user
 * Uses JSON format
 */
export async function register(userData: RegisterRequest): Promise<User> {
  // Transform to snake_case for backend
  const snakeCaseData = transformKeysToSnake(userData)

  const response = await axiosInstance.post<TokenResponse>(
    '/v1/auth/register',
    snakeCaseData
  )

  // Transform response from snake_case to camelCase
  const tokenData = transformKeysToCamel<TokenResponse>(response.data)

  // Store token in localStorage
  localStorage.setItem(TOKEN_KEY, tokenData.accessToken)

  // Fetch and return user data
  const user = await getCurrentUser()

  // Cache user in localStorage
  localStorage.setItem(USER_KEY, JSON.stringify(user))

  return user
}

/**
 * Get current authenticated user
 * Token is automatically injected by axios interceptor
 */
export async function getCurrentUser(): Promise<User> {
  const response = await axiosInstance.get<UserResponse>('/v1/auth/me')

  // Transform response from snake_case to camelCase
  const user = transformKeysToCamel<User>(response.data)

  return user
}

/**
 * Logout current user
 * Clears token and user data from localStorage
 */
export function logout(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * Get cached user from localStorage
 * Returns null if no user is cached
 */
export function getCachedUser(): User | null {
  const userJson = localStorage.getItem(USER_KEY)
  if (!userJson) {
    return null
  }

  try {
    return JSON.parse(userJson) as User
  } catch (error) {
    console.error('Failed to parse cached user:', error)
    localStorage.removeItem(USER_KEY)
    return null
  }
}

/**
 * Check if user has a valid token
 * Does not validate token with backend
 */
export function hasToken(): boolean {
  return localStorage.getItem(TOKEN_KEY) !== null
}

/**
 * Get stored token
 * Returns null if no token exists
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
