import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi, componentTemplateConfigsApi } from '../api'

export const useTemplates = (organizationUuid: string | undefined, category?: string) => {
  return useQuery({
    queryKey: ['templates', organizationUuid, category],
    queryFn: () => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return templatesApi.list(organizationUuid, category)
    },
    enabled: !!organizationUuid,
  })
}

export const useTemplate = (organizationUuid: string | undefined, uuid: string | undefined) => {
  return useQuery({
    queryKey: ['template', organizationUuid, uuid],
    queryFn: () => {
      if (!organizationUuid || !uuid) {
        throw new Error('Organization UUID and template UUID are required')
      }
      return templatesApi.get(organizationUuid, uuid)
    },
    enabled: !!organizationUuid && !!uuid,
  })
}

export const useCreateTemplate = (organizationUuid: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: import('../types').TemplateCreate) => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return templatesApi.create(organizationUuid, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates', organizationUuid] })
    },
  })
}

export const useUpdateTemplate = (organizationUuid: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: import('../types').TemplateUpdate }) => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return templatesApi.update(organizationUuid, uuid, data)
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['templates', organizationUuid] })
      queryClient.invalidateQueries({ queryKey: ['template', organizationUuid, variables.uuid] })
    },
  })
}

export const useDeleteTemplate = (organizationUuid: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (uuid: string) => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return templatesApi.delete(organizationUuid, uuid)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates', organizationUuid] })
    },
  })
}

export const useComponentTemplateConfigs = (organizationUuid: string | undefined, component_type?: string) => {
  return useQuery({
    queryKey: ['component-template-configs', organizationUuid, component_type],
    queryFn: () => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return componentTemplateConfigsApi.list(organizationUuid, component_type)
    },
    enabled: !!organizationUuid,
  })
}

export const useTemplatesForComponent = (organizationUuid: string | undefined, component_type: string | undefined) => {
  return useQuery({
    queryKey: ['templates-for-component', organizationUuid, component_type],
    queryFn: () => {
      if (!organizationUuid || !component_type) {
        throw new Error('Organization UUID and component type are required')
      }
      return componentTemplateConfigsApi.getTemplatesForComponent(organizationUuid, component_type)
    },
    enabled: !!organizationUuid && !!component_type,
  })
}

export const useTemplateSettingsForComponent = (
  organizationUuid: string | undefined,
  componentType: string | undefined,
) => {
  return useQuery({
    queryKey: ['template-settings', organizationUuid, componentType],
    queryFn: () => {
      if (!organizationUuid || !componentType) {
        throw new Error('Organization UUID and component type are required')
      }
      return componentTemplateConfigsApi.getTemplateSettings(organizationUuid, componentType)
    },
    enabled: !!organizationUuid && !!componentType,
  })
}
