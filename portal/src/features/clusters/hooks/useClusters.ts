import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clustersApi } from '../api'

export const useClusters = () => {
  return useQuery({
    queryKey: ['clusters'],
    queryFn: clustersApi.list,
  })
}

export const useCluster = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['cluster', uuid],
    queryFn: () => clustersApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateCluster = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: clustersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
    },
  })
}

export const useUpdateCluster = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: Partial<import('../types').ClusterCreate> }) =>
      clustersApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster', variables.uuid] })
    },
  })
}

export const useDeleteCluster = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: clustersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
    },
  })
}
