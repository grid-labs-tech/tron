export interface Application {
  uuid: string
  name: string
  repository?: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface ApplicationCreate {
  name: string
  repository?: string | null
  enabled?: boolean
}
