import { api } from '../../shared/api'
import type { Template, TemplateCreate, TemplateUpdate, ComponentTemplateConfig, ComponentTemplateConfigCreate, ComponentTemplateConfigUpdate } from './types'

export const templatesApi = {
  list: async (category?: string): Promise<Template[]> => {
    const params = category ? { category } : {}
    const response = await api.get<Template[]>('/templates/', { params })
    return response.data
  },
  get: async (uuid: string): Promise<Template> => {
    const response = await api.get<Template>(`/templates/${uuid}`)
    return response.data
  },
  create: async (data: TemplateCreate): Promise<Template> => {
    const response = await api.post<Template>('/templates/', data)
    return response.data
  },
  update: async (uuid: string, data: TemplateUpdate): Promise<Template> => {
    const response = await api.put<Template>(`/templates/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/templates/${uuid}`)
  },
}

export const componentTemplateConfigsApi = {
  list: async (component_type?: string): Promise<ComponentTemplateConfig[]> => {
    const params = component_type ? { component_type } : {}
    const response = await api.get<ComponentTemplateConfig[]>('/component-template-configs/', { params })
    return response.data
  },
  get: async (uuid: string): Promise<ComponentTemplateConfig> => {
    const response = await api.get<ComponentTemplateConfig>(`/component-template-configs/${uuid}`)
    return response.data
  },
  create: async (data: ComponentTemplateConfigCreate): Promise<ComponentTemplateConfig> => {
    const response = await api.post<ComponentTemplateConfig>('/component-template-configs/', data)
    return response.data
  },
  update: async (uuid: string, data: ComponentTemplateConfigUpdate): Promise<ComponentTemplateConfig> => {
    const response = await api.put<ComponentTemplateConfig>(`/component-template-configs/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/component-template-configs/${uuid}`)
  },
  getTemplatesForComponent: async (component_type: string): Promise<any[]> => {
    const response = await api.get(`/component-template-configs/component/${component_type}/templates`)
    return response.data
  },
}
