import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { cronComponentsApi } from '../api'

export const useCronComponents = () => {
  return useQuery({
    queryKey: ['cron-components'],
    queryFn: cronComponentsApi.list,
  })
}

export const useCronComponent = (uuid: string | undefined) => {
  return useQuery({
    queryKey: ['cron', uuid],
    queryFn: () => cronComponentsApi.get(uuid!),
    enabled: !!uuid,
  })
}

export const useCreateCronComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: cronComponentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cron-components'] })
    },
  })
}

export const useUpdateCronComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: Partial<import('../types').ApplicationComponentCreate> }) =>
      cronComponentsApi.update(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['cron-components'] })
      queryClient.invalidateQueries({ queryKey: ['cron', variables.uuid] })
    },
  })
}

export const useDeleteCronComponent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: cronComponentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cron-components'] })
    },
  })
}

export const useCronJobs = (uuid: string | undefined, refetchInterval?: number | false) => {
  return useQuery({
    queryKey: ['cron-jobs', uuid],
    queryFn: () => cronComponentsApi.getJobs(uuid!),
    enabled: !!uuid,
    refetchInterval: refetchInterval !== undefined ? refetchInterval : false,
  })
}

export const useCronJobLogs = (uuid: string | undefined, jobName: string | undefined, containerName?: string, tailLines: number = 100, refetchInterval?: number | false) => {
  return useQuery({
    queryKey: ['cron-job-logs', uuid, jobName, containerName, tailLines],
    queryFn: () => cronComponentsApi.getJobLogs(uuid!, jobName!, containerName, tailLines),
    enabled: !!uuid && !!jobName,
    refetchInterval: refetchInterval !== undefined ? refetchInterval : false,
  })
}

export const useDeleteCronJob = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, jobName }: { uuid: string; jobName: string }) =>
      cronComponentsApi.deleteJob(uuid, jobName),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['cron-jobs', variables.uuid] })
    },
  })
}
