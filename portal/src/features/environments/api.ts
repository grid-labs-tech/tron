import { api } from '../../shared/api'
import type { Environment, EnvironmentCreate } from './types'

export const environmentsApi = {
  list: async (): Promise<Environment[]> => {
    const response = await api.get<Environment[]>('/environments/')
    return response.data
  },
  get: async (uuid: string): Promise<Environment> => {
    const response = await api.get<Environment>(`/environments/${uuid}`)
    return response.data
  },
  create: async (data: EnvironmentCreate): Promise<Environment> => {
    const response = await api.post<Environment>('/environments/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<EnvironmentCreate>): Promise<Environment> => {
    const response = await api.put<Environment>(`/environments/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/environments/${uuid}`)
  },
}
