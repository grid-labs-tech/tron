export interface Environment {
  uuid: string
  name: string
  created_at: string
  updated_at: string
}

export interface EnvironmentCreate {
  name: string
}
