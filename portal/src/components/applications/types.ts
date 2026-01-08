export interface WebappSettings {
  custom_metrics: {
    enabled: boolean
    path: string
    port: number
  }
  exposure: {
    type: 'http' | 'tcp' | 'udp'
    port: number
    visibility: 'cluster' | 'private' | 'public'
  }
  envs: Array<{
    key: string
    value: string
  }>
  command: string | null
  cpu_scaling_threshold: number
  memory_scaling_threshold: number
  healthcheck: {
    path: string
    protocol: 'http' | 'tcp'
    port: number
    timeout: number
    interval: number
    initial_interval: number
    failure_threshold: number
  }
  cpu: number
  memory: number
  autoscaling: {
    min: number
    max: number
  }
}

export interface CronSettings {
  envs: Array<{
    key: string
    value: string
  }>
  command: string | null
  cpu: number
  memory: number
  schedule: string
}

export interface WorkerSettings {
  custom_metrics: {
    enabled: boolean
    path: string
    port: number
  }
  envs: Array<{
    key: string
    value: string
  }>
  command: string | null
  cpu: number
  memory: number
  cpu_scaling_threshold: number
  memory_scaling_threshold: number
  autoscaling: {
    min: number
    max: number
  }
}

export type VisibilityType = 'public' | 'private' | 'cluster'

export interface ComponentFormData {
  name: string
  type: 'webapp' | 'worker' | 'cron'
  url: string | null
  visibility?: VisibilityType // Optional, only used for worker (legacy), webapp uses settings.exposure.visibility
  enabled: boolean
  settings: WebappSettings | CronSettings | WorkerSettings | null
}

export const getDefaultWebappSettings = (): WebappSettings => ({
  custom_metrics: {
    enabled: false,
    path: '/metrics',
    port: 8080,
  },
  exposure: {
    type: 'http',
    port: 80,
    visibility: 'cluster',
  },
  envs: [],
  command: null,
  cpu_scaling_threshold: 80,
  memory_scaling_threshold: 80,
  healthcheck: {
    path: '/healthcheck',
    protocol: 'http',
    port: 80,
    timeout: 3,
    interval: 15,
    initial_interval: 15,
    failure_threshold: 2,
  },
  cpu: 0.5,
  memory: 512,
  autoscaling: {
    min: 2,
    max: 10,
  },
})

export const getDefaultCronSettings = (): CronSettings => ({
  envs: [],
  command: null,
  cpu: 0.5,
  memory: 512,
  schedule: '0 0 * * *', // Daily at midnight
})

export const getDefaultWorkerSettings = (): WorkerSettings => ({
  custom_metrics: {
    enabled: false,
    path: '/metrics',
    port: 8080,
  },
  envs: [],
  command: null,
  cpu: 0.5,
  memory: 512,
  cpu_scaling_threshold: 80,
  memory_scaling_threshold: 80,
  autoscaling: {
    min: 2,
    max: 10,
  },
})

