export type TemplateSettingType = 'boolean' | 'string'

export interface TemplateSettingDefinition {
  name: string
  description?: string | null
  type: TemplateSettingType
}

export interface Template {
  uuid: string
  name: string
  slug: string
  description?: string
  category: string
  content: string
  variables_schema?: string
  template_settings: TemplateSettingDefinition[]
  created_at: string
  updated_at: string
}

export interface TemplateCreate {
  name: string
  description?: string
  category: string
  content: string
  variables_schema?: string
  template_settings?: TemplateSettingDefinition[]
}

export interface TemplateUpdate {
  name?: string
  description?: string
  content?: string
  variables_schema?: string
  template_settings?: TemplateSettingDefinition[]
}

export interface ComponentTemplateConfig {
  uuid: string
  component_type: string
  template_uuid: string
  render_order: number
  enabled: boolean
  template_name?: string
}

export interface ComponentTemplateConfigCreate {
  component_type: string
  template_uuid: string
  render_order: number
  enabled: boolean
}

export interface ComponentTemplateConfigUpdate {
  render_order?: number
  enabled?: boolean
}
