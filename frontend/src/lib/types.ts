import type { components } from './openapi-types'

export type LoginData = components['schemas']['LoginRequest']

// Form shape (includes confirmPassword)
export interface RegisterData {
  email: string
  password: string
  confirmPassword: string
}

// API payload shape for registration
export type RegisterPayload = components['schemas']['RegisterRequest']

export type User = components['schemas']['UserResponse'] & { created_at?: string }

export interface ApiError {
  detail?: string
  message?: string
  code?: string
}

// Prefer generated type; intersect with precise shape to ensure strong typing
export type DashboardData = components['schemas']['DashboardData'] & {
  user_stats: {
    user_id: number
    email: string
    account_created: string
  }
  system_metrics: {
    total_users: number
    active_users: number
    pending_resets: number
  }
}
