export type VisibilityType = 'public' | 'private' | 'cluster'

export interface ApplicationComponent {
  uuid: string
  name: string
  type: 'webapp' | 'worker' | 'cron'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  settings: Record<string, any> | null
  visibility: VisibilityType
  url: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface ApplicationComponentCreate {
  instance_uuid: string
  name: string
  type: 'webapp' | 'worker' | 'cron'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  settings?: Record<string, any> | null
  visibility?: VisibilityType
  url?: string | null
  enabled?: boolean
}

export interface Pod {
  name: string
  status: string
  restarts: number
  cpu_requests: number
  cpu_limits: number
  memory_requests: number  // em MB
  memory_limits: number  // em MB
  age_seconds: number
  host_ip: string | null
}

export interface PodLogs {
  logs: string
  pod_name: string
  container_name?: string | null
}

export interface PodCommandResponse {
  stdout: string
  stderr: string
  return_code: number
}

export interface CronJob {
  name: string
  status: string  // Succeeded, Failed, Active, Unknown
  succeeded: number
  failed: number
  active: number
  start_time: string | null
  completion_time: string | null
  age_seconds: number
  duration_seconds: number | null
}

export interface CronJobLogs {
  logs: string
  pod_name: string
  job_name: string
  container_name: string | null
}
