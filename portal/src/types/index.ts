export interface GatewayApiReference {
  namespace: string
  name: string
}

export interface GatewayApi {
  enabled: boolean
  resources: string[]
}

export interface GatewayFeatures {
  api: GatewayApi
  reference: GatewayApiReference
}

export interface Cluster {
  uuid: string
  name: string
  api_address: string
  environment_uuid: string
  environment?: Environment // Adicionado para incluir o objeto environment
  detail?: {
    status: string
    message?: {
      code: string
      message: string
    }
  }
  gateway?: GatewayFeatures
  created_at: string
  updated_at: string
}

export interface ClusterCreate {
  name: string
  api_address: string
  token: string
  environment_uuid: string
}

export interface Environment {
  uuid: string
  name: string
  created_at: string
  updated_at: string
}

export interface EnvironmentCreate {
  name: string
}

export interface Namespace {
  uuid: string
  name: string
  created_at: string
  updated_at: string
}

export interface NamespaceCreate {
  name: string
}

export interface Workload {
  uuid: string
  name: string
  created_at: string
  updated_at: string
}

export interface WorkloadCreate {
  name: string
}

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

export interface WebappDeploy {
  uuid: string
  webapp_uuid: string
  environment_uuid: string
  workload_uuid: string
  image: string
  version: string
  cpu: number
  memory: number
  cpu_scaling_threshold: number
  memory_scaling_threshold: number
  custom_metrics: Record<string, any>
  endpoints: Record<string, any>
  envs: Array<{ key: string; value: string }> | null
  command: string | null
  healthcheck: Record<string, any>
  created_at: string
  updated_at: string
}

export interface WebappDeployCreate {
  webapp_uuid: string
  environment_uuid: string
  workload_uuid: string
  image: string
  version: string
  cpu: number
  memory: number
  cpu_scaling_threshold: number
  memory_scaling_threshold: number
  custom_metrics: Record<string, any>
  endpoints: Record<string, any>
  envs: Array<{ key: string; value: string }> | null
  command: string | null
  healthcheck: Record<string, any>
}

export interface Template {
  uuid: string
  name: string
  description?: string
  category: string
  content: string
  variables_schema?: string
  created_at: string
  updated_at: string
}

export interface TemplateCreate {
  name: string
  description?: string
  category: string
  content: string
  variables_schema?: string
}

export interface TemplateUpdate {
  name?: string
  description?: string
  content?: string
  variables_schema?: string
}

export interface ComponentTemplateConfig {
  uuid: string
  component_type: string
  template_uuid: string
  render_order: number
  enabled: boolean
  template_name?: string
}

export interface ComponentTemplateConfigCreate {
  component_type: string
  template_uuid: string
  render_order: number
  enabled: boolean
}

export interface ComponentTemplateConfigUpdate {
  render_order?: number
  enabled?: boolean
}

export type VisibilityType = 'public' | 'private' | 'cluster'

export interface ApplicationComponent {
  uuid: string
  name: string
  type: 'webapp' | 'worker' | 'cron'
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
  settings?: Record<string, any> | null
  visibility?: VisibilityType
  url?: string | null
  enabled?: boolean
}

export interface InstanceComponent {
  uuid: string
  name: string
  type: string
  settings: Record<string, any> | null
  url: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface Instance {
  uuid: string
  application: Application
  environment: Environment
  components: InstanceComponent[]
  image: string
  version: string
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface InstanceCreate {
  application_uuid: string
  environment_uuid: string
  image: string
  version: string
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

export interface PodCommandRequest {
  command: string[]
  container_name?: string | null
}

export interface PodCommandResponse {
  stdout: string
  stderr: string
  return_code: number
}

// Auth types
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

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
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

// Dashboard
export interface ComponentStats {
  total: number
  webapp: number
  worker: number
  cron: number
  enabled: number
  disabled: number
}

export interface DashboardOverview {
  applications: number
  instances: number
  components: ComponentStats
  clusters: number
  environments: number
  components_by_environment: Record<string, number>
  components_by_cluster: Record<string, number>
}

export interface KubernetesEventInvolvedObject {
  kind: string | null
  name: string | null
  namespace: string | null
}

export interface KubernetesEventSource {
  component: string | null
  host: string | null
}

export interface KubernetesEvent {
  name: string
  namespace: string
  type: string // Normal, Warning
  reason: string
  message: string
  involved_object: KubernetesEventInvolvedObject
  source: KubernetesEventSource
  first_timestamp: string | null
  last_timestamp: string | null
  count: number
  age_seconds: number
}

