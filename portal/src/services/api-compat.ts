// Temporary compatibility file to help with migration
// This file re-exports from the new feature-based API structure
// This allows gradual migration of imports without breaking everything at once

// Applications
export { applicationsApi } from '../features/applications'
export type { Application, ApplicationCreate } from '../features/applications'

// Clusters
export { clustersApi } from '../features/clusters'
export type { Cluster, ClusterCreate } from '../features/clusters'

// Environments
export { environmentsApi } from '../features/environments'
export type { Environment, EnvironmentCreate } from '../features/environments'

// Instances
export { instancesApi } from '../features/instances'
export type { Instance, InstanceCreate, KubernetesEvent } from '../features/instances'

// Auth
export { authApi } from '../features/auth'
export type { User, UserCreate, LoginRequest, RefreshTokenRequest, UpdateProfileRequest, Token } from '../features/auth'

// Users
export { usersApi } from '../features/users'
export type { User as UserType, UserCreate as UserCreateType } from '../features/users'

// Tokens
export { tokensApi } from '../features/tokens'
export type { ApiToken, ApiTokenCreate, ApiTokenUpdate, ApiTokenCreateResponse } from '../features/tokens'

// Templates
export { templatesApi, componentTemplateConfigsApi } from '../features/templates'
export type { Template, TemplateCreate, TemplateUpdate, ComponentTemplateConfig, ComponentTemplateConfigCreate, ComponentTemplateConfigUpdate } from '../features/templates'

// Dashboard
export { dashboardApi } from '../features/dashboard'
export type { DashboardOverview } from '../features/dashboard'

// Components
import { webappComponentsApi, cronComponentsApi, workerComponentsApi } from '../features/components'
export { webappComponentsApi, cronComponentsApi, workerComponentsApi }
export type { ApplicationComponent, ApplicationComponentCreate, Pod, PodLogs, PodCommandResponse, CronJob, CronJobLogs, VisibilityType } from '../features/components'

// Legacy exports for backward compatibility
export const applicationComponentsApi = webappComponentsApi
export const cronsApi = cronComponentsApi
export const workersApi = workerComponentsApi

// Re-export api client
export { api } from '../shared/api'
