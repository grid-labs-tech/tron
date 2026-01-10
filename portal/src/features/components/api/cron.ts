import { api } from '../../../shared/api'
import type { ApplicationComponent, ApplicationComponentCreate, CronJob, CronJobLogs } from '../types'

export const cronComponentsApi = {
  list: async (): Promise<ApplicationComponent[]> => {
    const response = await api.get<ApplicationComponent[]>('/application_components/cron/')
    return response.data
  },
  get: async (uuid: string): Promise<ApplicationComponent> => {
    const response = await api.get<ApplicationComponent>(`/application_components/cron/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationComponentCreate): Promise<ApplicationComponent> => {
    const response = await api.post<ApplicationComponent>('/application_components/cron/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationComponentCreate>): Promise<ApplicationComponent> => {
    const response = await api.put<ApplicationComponent>(`/application_components/cron/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/application_components/cron/${uuid}`)
  },
  getJobs: async (uuid: string): Promise<CronJob[]> => {
    const response = await api.get<CronJob[]>(`/application_components/cron/${uuid}/jobs`)
    return response.data
  },
  getJobLogs: async (uuid: string, jobName: string, containerName?: string, tailLines: number = 100): Promise<CronJobLogs> => {
    const params = new URLSearchParams()
    if (containerName) {
      params.append('container_name', containerName)
    }
    params.append('tail_lines', tailLines.toString())
    const response = await api.get<CronJobLogs>(`/application_components/cron/${uuid}/jobs/${jobName}/logs?${params.toString()}`)
    return response.data
  },
  deleteJob: async (uuid: string, jobName: string): Promise<void> => {
    await api.delete(`/application_components/cron/${uuid}/jobs/${jobName}`)
  },
}
