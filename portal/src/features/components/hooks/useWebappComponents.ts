import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { webappComponentsApi } from '../api'

export const useWebappComponents = () => {
  return useQuery({
    queryKey: ['webapp-components'],
    queryFn: webappComponentsApi.list,
  })
}

export const useWebappComponent = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['webapp', uuid],
    queryFn: () => webappComponentsApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateWebappComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: webappComponentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webapp-components'] })
    },
  })
}

export const useUpdateWebappComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: Partial<import('../types').ApplicationComponentCreate> }) =>
      webappComponentsApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['webapp-components'] })
      queryClient.invalidateQueries({ queryKey: ['webapp', variables.uuid] })
    },
  })
}

export const useDeleteWebappComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: webappComponentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webapp-components'] })
    },
  })
}

export const useWebappPods = (uuid: string | undefined, refetchInterval?: number | false) => {
  return useQuery({
    queryKey: ['webapp-pods', uuid],
    queryFn: () => webappComponentsApi.getPods(uuid!),
    enabled: !!uuid,
    refetchInterval: refetchInterval !== undefined ? refetchInterval : false,
  })
}

export const useDeleteWebappPod = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, podName }: { uuid: string; podName: string }) =>
      webappComponentsApi.deletePod(uuid, podName),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['webapp-pods', variables.uuid] })
    },
  })
}

export const useWebappPodLogs = (uuid: string | undefined, podName: string | undefined, containerName?: string, tailLines: number = 100, refetchInterval?: number | false) => {
  return useQuery({
    queryKey: ['webapp-pod-logs', uuid, podName, containerName, tailLines],
    queryFn: () => webappComponentsApi.getPodLogs(uuid!, podName!, containerName, tailLines),
    enabled: !!uuid && !!podName,
    refetchInterval: refetchInterval !== undefined ? refetchInterval : false,
  })
}

export const useExecWebappPodCommand = () => {
  return useMutation({
    mutationFn: ({ uuid, podName, command, containerName }: { uuid: string; podName: string; command: string[]; containerName?: string }) =>
      webappComponentsApi.execPodCommand(uuid, podName, command, containerName),
  })
}
