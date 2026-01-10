import { api } from '../../shared/api'
import type { Application, ApplicationCreate } from './types'

export const applicationsApi = {
  list: async (): Promise<Application[]> => {
    const response = await api.get<Application[]>('/applications/')
    return response.data
  },
  get: async (uuid: string): Promise<Application> => {
    const response = await api.get<Application>(`/applications/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationCreate): Promise<Application> => {
    const response = await api.post<Application>('/applications/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationCreate>): Promise<Application> => {
    const response = await api.put<Application>(`/applications/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/applications/${uuid}`)
  },
}
