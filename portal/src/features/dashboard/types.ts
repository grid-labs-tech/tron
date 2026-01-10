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
