import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { instancesApi } from '../api'

export const useInstances = () => {
  return useQuery({
    queryKey: ['instances'],
    queryFn: instancesApi.list,
  })
}

export const useInstance = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['instances', uuid],
    queryFn: () => instancesApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateInstance = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: instancesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] })
    },
  })
}

export const useUpdateInstance = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: Partial<import('../types').InstanceCreate> }) =>
      instancesApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['instances'] })
      queryClient.invalidateQueries({ queryKey: ['instances', variables.uuid] })
    },
  })
}

export const useDeleteInstance = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: instancesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] })
    },
  })
}

export const useInstanceEvents = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['instances', uuid, 'events'],
    queryFn: () => instancesApi.getEvents(uuid!),
    enabled: !!uuid,
  })
}

export const useSyncInstance = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: instancesApi.sync,
    onSuccess: (_, uuid) => {
      queryClient.invalidateQueries({ queryKey: ['instances', uuid] })
    },
  })
}
