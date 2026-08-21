import { api } from '../../shared/api'
import type { EnvironmentCrossplaneConfig, EnvironmentCrossplaneConfigUpdate } from './types'

export const crossplaneApi = {
  get: async (
    organizationUuid: string,
    environmentUuid: string
  ): Promise<EnvironmentCrossplaneConfig> => {
    const response = await api.get<EnvironmentCrossplaneConfig>(
      `/organizations/${organizationUuid}/environments/${environmentUuid}/crossplane`
    )
    return response.data
  },
  update: async (
    organizationUuid: string,
    environmentUuid: string,
    data: EnvironmentCrossplaneConfigUpdate
  ): Promise<EnvironmentCrossplaneConfig> => {
    const response = await api.put<EnvironmentCrossplaneConfig>(
      `/organizations/${organizationUuid}/environments/${environmentUuid}/crossplane`,
      data
    )
    return response.data
  },
}
