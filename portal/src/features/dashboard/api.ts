import { api } from '../../shared/api'
import type { DashboardOverview } from './types'

export const dashboardApi = {
  getOverview: async (): Promise<DashboardOverview> => {
    const response = await api.get<DashboardOverview>('/dashboard/')
    return response.data
  },
}
