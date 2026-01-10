import { api } from '../../../shared/api'
import type { ApplicationComponent, ApplicationComponentCreate } from '../types'

export const workerComponentsApi = {
  list: async (): Promise<ApplicationComponent[]> => {
    const response = await api.get<ApplicationComponent[]>('/application_components/worker/')
    return response.data
  },
  get: async (uuid: string): Promise<ApplicationComponent> => {
    const response = await api.get<ApplicationComponent>(`/application_components/worker/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationComponentCreate): Promise<ApplicationComponent> => {
    const response = await api.post<ApplicationComponent>('/application_components/worker/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationComponentCreate>): Promise<ApplicationComponent> => {
    const response = await api.put<ApplicationComponent>(`/application_components/worker/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/application_components/worker/${uuid}`)
  },
}
