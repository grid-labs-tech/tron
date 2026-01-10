import type { UserRole } from '../auth/types'

export interface ApiToken {
  uuid: string
  name: string
  role: UserRole
  is_active: boolean
  last_used_at: string | null
  expires_at: string | null
  created_at: string
  updated_at: string
  user_id: number | null
}

export interface ApiTokenCreate {
  name: string
  role: UserRole
  expires_at?: string | null
}

export interface ApiTokenUpdate {
  name?: string | null
  role?: UserRole | null
  is_active?: boolean | null
  expires_at?: string | null
}

export interface ApiTokenCreateResponse {
  uuid: string
  name: string
  token: string
  role: UserRole
  expires_at: string | null
  created_at: string
}
