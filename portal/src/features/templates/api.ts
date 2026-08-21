import { api } from '../../shared/api'
import type { Template, TemplateCreate, TemplateUpdate, ComponentTemplateConfig, ComponentTemplateConfigCreate, ComponentTemplateConfigUpdate } from './types'

export const templatesApi = {
  list: async (organizationUuid: string, category?: string): Promise<Template[]> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const params = category ? { category } : {}
    const response = await api.get<Template[]>(`/organizations/${organizationUuid}/templates/`, { params })
    return response.data
  },
  get: async (organizationUuid: string, uuid: string): Promise<Template> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.get<Template>(`/organizations/${organizationUuid}/templates/${uuid}`)
    return response.data
  },
  create: async (organizationUuid: string, data: TemplateCreate): Promise<Template> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.post<Template>(`/organizations/${organizationUuid}/templates/`, data)
    return response.data
  },
  update: async (organizationUuid: string, uuid: string, data: TemplateUpdate): Promise<Template> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.put<Template>(`/organizations/${organizationUuid}/templates/${uuid}`, data)
    return response.data
  },
  delete: async (organizationUuid: string, uuid: string): Promise<void> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    await api.delete(`/organizations/${organizationUuid}/templates/${uuid}`)
  },
}

export const componentTemplateConfigsApi = {
  list: async (organizationUuid: string, component_type?: string): Promise<ComponentTemplateConfig[]> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const params = component_type ? { component_type } : {}
    const response = await api.get<ComponentTemplateConfig[]>(`/organizations/${organizationUuid}/component-template-configs/`, { params })
    return response.data
  },
  get: async (organizationUuid: string, uuid: string): Promise<ComponentTemplateConfig> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.get<ComponentTemplateConfig>(`/organizations/${organizationUuid}/component-template-configs/${uuid}`)
    return response.data
  },
  create: async (organizationUuid: string, data: ComponentTemplateConfigCreate): Promise<ComponentTemplateConfig> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.post<ComponentTemplateConfig>(`/organizations/${organizationUuid}/component-template-configs/`, data)
    return response.data
  },
  update: async (organizationUuid: string, uuid: string, data: ComponentTemplateConfigUpdate): Promise<ComponentTemplateConfig> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.put<ComponentTemplateConfig>(`/organizations/${organizationUuid}/component-template-configs/${uuid}`, data)
    return response.data
  },
  delete: async (organizationUuid: string, uuid: string): Promise<void> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    await api.delete(`/organizations/${organizationUuid}/component-template-configs/${uuid}`)
  },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getTemplatesForComponent: async (organizationUuid: string, component_type: string): Promise<any[]> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.get(`/organizations/${organizationUuid}/component-template-configs/component/${component_type}/templates`)
    return response.data
  },
  getTemplateSettings: async (organizationUuid: string, componentType: string): Promise<import('./types').TemplateSettingsGroup[]> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.get<import('./types').TemplateSettingsGroup[]>(
      `/organizations/${organizationUuid}/component-template-configs/component/${componentType}/template-settings`
    )
    return response.data
  },
}
