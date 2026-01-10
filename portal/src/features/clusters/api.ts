import { api } from '../../shared/api'
import type { Cluster, ClusterCreate } from './types'

export const clustersApi = {
  list: async (): Promise<Cluster[]> => {
    const response = await api.get<Cluster[]>('/clusters/')
    return response.data
  },
  get: async (uuid: string): Promise<Cluster> => {
    const response = await api.get<Cluster>(`/clusters/${uuid}`)
    return response.data
  },
  create: async (data: ClusterCreate): Promise<Cluster> => {
    const response = await api.post<Cluster>('/clusters/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ClusterCreate>): Promise<Cluster> => {
    const response = await api.put<Cluster>(`/clusters/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/clusters/${uuid}`)
  },
}
