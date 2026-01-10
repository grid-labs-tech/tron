import { api } from '../../../shared/api'
import type { ApplicationComponent, ApplicationComponentCreate, Pod, PodLogs, PodCommandResponse } from '../types'

export const webappComponentsApi = {
  list: async (): Promise<ApplicationComponent[]> => {
    const response = await api.get<ApplicationComponent[]>('/application_components/webapp/')
    return response.data
  },
  get: async (uuid: string): Promise<ApplicationComponent> => {
    const response = await api.get<ApplicationComponent>(`/application_components/webapp/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationComponentCreate): Promise<ApplicationComponent> => {
    if (data.type && data.type !== 'webapp') {
      throw new Error(`Component type ${data.type} is not yet supported. Only 'webapp' is available.`)
    }
    const response = await api.post<ApplicationComponent>('/application_components/webapp/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationComponentCreate>): Promise<ApplicationComponent> => {
    const response = await api.put<ApplicationComponent>(`/application_components/webapp/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/application_components/webapp/${uuid}`)
  },
  getPods: async (uuid: string): Promise<Pod[]> => {
    const response = await api.get<Pod[]>(`/application_components/webapp/${uuid}/pods`)
    return response.data
  },
  deletePod: async (uuid: string, podName: string): Promise<void> => {
    await api.delete(`/application_components/webapp/${uuid}/pods/${podName}`)
  },
  getPodLogs: async (uuid: string, podName: string, containerName?: string, tailLines: number = 100): Promise<PodLogs> => {
    const params = new URLSearchParams()
    if (containerName) {
      params.append('container_name', containerName)
    }
    params.append('tail_lines', tailLines.toString())
    const response = await api.get<PodLogs>(`/application_components/webapp/${uuid}/pods/${podName}/logs?${params.toString()}`)
    return response.data
  },
  execPodCommand: async (uuid: string, podName: string, command: string[], containerName?: string): Promise<PodCommandResponse> => {
    const response = await api.post<PodCommandResponse>(`/application_components/webapp/${uuid}/pods/${podName}/exec`, {
      command,
      container_name: containerName,
    })
    return response.data
  },
}
