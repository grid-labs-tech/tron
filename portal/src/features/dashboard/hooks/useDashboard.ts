import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../api'

export const useDashboardOverview = () => {
  return useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: dashboardApi.getOverview,
  })
}
