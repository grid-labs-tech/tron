import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workerComponentsApi } from '../api'

export const useWorkerComponents = () => {
  return useQuery({
    queryKey: ['worker-components'],
    queryFn: workerComponentsApi.list,
  })
}

export const useWorkerComponent = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['worker', uuid],
    queryFn: () => workerComponentsApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateWorkerComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: workerComponentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worker-components'] })
    },
  })
}

export const useUpdateWorkerComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: Partial<import('../types').ApplicationComponentCreate> }) =>
      workerComponentsApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['worker-components'] })
      queryClient.invalidateQueries({ queryKey: ['worker', variables.uuid] })
    },
  })
}

export const useDeleteWorkerComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: workerComponentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worker-components'] })
    },
  })
}
