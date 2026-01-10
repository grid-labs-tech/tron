import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi, componentTemplateConfigsApi } from '../api'

export const useTemplates = (category?: string) => {
  return useQuery({
    queryKey: ['templates', category],
    queryFn: () => templatesApi.list(category),
  })
}

export const useTemplate = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['template', uuid],
    queryFn: () => templatesApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: templatesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export const useUpdateTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: import('../types').TemplateUpdate }) =>
      templatesApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      queryClient.invalidateQueries({ queryKey: ['template', variables.uuid] })
    },
  })
}

export const useDeleteTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: templatesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export const useComponentTemplateConfigs = (component_type?: string) => {
  return useQuery({
    queryKey: ['component-template-configs', component_type],
    queryFn: () => componentTemplateConfigsApi.list(component_type),
  })
}

export const useTemplatesForComponent = (component_type: string | undefined) => {
  return useQuery({
    queryKey: ['templates-for-component', component_type],
    queryFn: () => componentTemplateConfigsApi.getTemplatesForComponent(component_type!),
    enabled: !!component_type,
  })
}
