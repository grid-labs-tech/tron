import { api } from '../../shared/api'
import type { Instance, InstanceCreate, KubernetesEvent } from './types'

export const instancesApi = {
  list: async (): Promise<Instance[]> => {
    const response = await api.get<Instance[]>('/instances/')
    return response.data
  },
  get: async (uuid: string): Promise<Instance> => {
    const response = await api.get<Instance>(`/instances/${uuid}`)
    return response.data
  },
  create: async (data: InstanceCreate): Promise<Instance> => {
    const response = await api.post<Instance>('/instances/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<InstanceCreate>): Promise<Instance> => {
    const response = await api.put<Instance>(`/instances/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/instances/${uuid}`)
  },
  getEvents: async (uuid: string): Promise<KubernetesEvent[]> => {
    const response = await api.get<KubernetesEvent[]>(`/instances/${uuid}/events`)
    return response.data
  },
  sync: async (uuid: string): Promise<{ detail: string; synced_components: number; total_components: number; errors: Array<{ component: string; error: string }> }> => {
    const response = await api.post(`/instances/${uuid}/sync`)
    return response.data
  },
}
