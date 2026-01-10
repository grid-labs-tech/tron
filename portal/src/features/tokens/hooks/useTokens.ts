import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tokensApi } from '../api'

export const useTokens = (params?: { skip?: number; limit?: number; search?: string }) => {
  return useQuery({
    queryKey: ['tokens', params],
    queryFn: () => tokensApi.list(params),
  })
}

export const useToken = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['token', uuid],
    queryFn: () => tokensApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateToken = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tokensApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
    },
  })
}

export const useUpdateToken = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: import('../types').ApiTokenUpdate }) =>
      tokensApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      queryClient.invalidateQueries({ queryKey: ['token', variables.uuid] })
    },
  })
}

export const useDeleteToken = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tokensApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
    },
  })
}
