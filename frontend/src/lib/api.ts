import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { LoginData, RegisterPayload, User } from '@/lib/types'

// Refresh lock to prevent concurrent refresh requests
let refreshPromise: Promise<void> | null = null

// Enhanced fetch with automatic token refresh
async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const response = await fetch(url, options)

  // If we get a 401, try refreshing the token and retry once
  if (response.status === 401 && url !== '/api/auth/refresh') {
    try {
      // If a refresh is already in progress, wait for it
      if (refreshPromise) {
        await refreshPromise
      } else {
        // Start a new refresh
        refreshPromise = fetch('/api/auth/refresh', { method: 'POST' })
          .then(refreshResponse => {
            if (!refreshResponse.ok) {
              throw new Error('Refresh failed')
            }
          })
          .finally(() => {
            refreshPromise = null
          })

        await refreshPromise
      }

      // Retry the original request with the new access token
      return await fetch(url, options)
    } catch (refreshError) {
      // If refresh fails, redirect to login
      window.location.href = '/auth/login'
      throw new Error('Authentication failed')
    }
  }

  return response
}

// API client functions
const apiClient = {
  async login(data: LoginData): Promise<User> {
    const response = await fetch('/api/auth/login/onsubmit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.message || 'Login failed')
    }
    const json = await response.json()
    return json.user as User
  },

  async getCurrentUser(): Promise<User> {
    const response = await fetchWithAuth('/api/auth/me')
    if (!response.ok) {
      const err: any = new Error('Not authenticated')
      err.status = response.status
      throw err
    }
    return response.json()
  },

  async register(data: RegisterPayload): Promise<User> {
    const response = await fetch('/api/auth/register/onsubmit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.message || 'Registration failed')
    }
    const json = await response.json()
    return json.user as User
  },

  async logout(): Promise<void> {
    await fetchWithAuth('/api/auth/logout/onsubmit', { method: 'POST' })
  },

  async refreshToken(): Promise<void> {
    const response = await fetch('/api/auth/refresh', { method: 'POST' })
    if (!response.ok) {
      throw new Error('Token refresh failed')
    }
  },

  async resetRequest(email: string): Promise<void> {
    const response = await fetch('/api/auth/reset/onsubmit/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.message || 'Reset request failed')
    }
  },

  async resetConfirm(token: string, newPassword: string): Promise<void> {
    const response = await fetch('/api/auth/reset/onsubmit/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password: newPassword }),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.message || 'Password reset failed')
    }
  },

  async getPageData(page: string): Promise<any> {
    const response = await fetchWithAuth(`/api/${page}/onload`)
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || error.message || `Failed to load ${page} data`)
    }
    return response.json()
  }
}

// Export the api object for use in route loaders
export const api = {
  auth: apiClient,
  getPageData: apiClient.getPageData,
}

// Auth hooks
export function useAuth() {
  const queryClient = useQueryClient()

  const login = useMutation({
    mutationFn: apiClient.login,
    onSuccess: (user) => {
      queryClient.setQueryData(['user'], user)
    },
  })

  const register = useMutation({
    mutationFn: apiClient.register,
    onSuccess: (user) => {
      queryClient.setQueryData(['user'], user)
    },
  })

  const logout = useMutation({
    mutationFn: apiClient.logout,
    onSuccess: () => {
      queryClient.clear()
    },
  })

  const refresh = useMutation({
    mutationFn: apiClient.refreshToken,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })

  const userQuery = useQuery({
    queryKey: ['user'],
    queryFn: apiClient.getCurrentUser,
    retry: false,
  })

  return {
    login,
    register,
    logout,
    refresh,
    user: userQuery.data,
    isAuthenticated: !!userQuery.data && !userQuery.isError,
    isLoading: userQuery.isLoading
  }
}

// Page data hook
export function usePageData(page: string) {
  return useQuery({
    queryKey: ['pageData', page],
    queryFn: () => apiClient.getPageData(page),
    retry: (failureCount, error: any) => {
      if (error?.status === 401) return false
      return failureCount < 3
    }
  })
}
