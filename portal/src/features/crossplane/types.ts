export interface EnvironmentCrossplaneConfig {
  enabled: boolean
  cluster_uuid: string | null
  aws_region: string
  aws_account_id: string
  provider_config: string
}

export type EnvironmentCrossplaneConfigUpdate = EnvironmentCrossplaneConfig
