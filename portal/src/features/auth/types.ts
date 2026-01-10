import type { Token } from '../../shared/types'

export type UserRole = 'admin' | 'user' | 'viewer'

export interface User {
  uuid: string
  email: string
  full_name: string | null
  is_active: boolean
  role: UserRole
  avatar_url: string | null
  created_at: string
  updated_at: string
}

export interface UserCreate {
  email: string
  password: string
  full_name?: string | null
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface UpdateProfileRequest {
  email?: string | null
  full_name?: string | null
  password?: string | null
  current_password?: string | null
}

export type { Token }
