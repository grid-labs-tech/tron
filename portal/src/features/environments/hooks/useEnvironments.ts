import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { environmentsApi } from '../api'

export const useEnvironments = () => {
  return useQuery({
    queryKey: ['environments'],
    queryFn: environmentsApi.list,
  })
}

export const useEnvironment = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['environment', uuid],
    queryFn: () => environmentsApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateEnvironment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: environmentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] })
    },
  })
}

export const useUpdateEnvironment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: Partial<import('../types').EnvironmentCreate> }) =>
      environmentsApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['environments'] })
      queryClient.invalidateQueries({ queryKey: ['environment', variables.uuid] })
    },
  })
}

export const useDeleteEnvironment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: environmentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] })
    },
  })
}
