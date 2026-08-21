import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { crossplaneApi } from '../api'
import type { EnvironmentCrossplaneConfigUpdate } from '../types'

export const useCrossplaneConfig = (
  organizationUuid: string | undefined,
  environmentUuid: string | undefined
) => {
  return useQuery({
    queryKey: ['crossplane-config', organizationUuid, environmentUuid],
    queryFn: () => crossplaneApi.get(organizationUuid!, environmentUuid!),
    enabled: !!organizationUuid && !!environmentUuid,
  })
}

export const useUpdateCrossplaneConfig = (organizationUuid: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      environmentUuid,
      config,
    }: {
      environmentUuid: string
      config: EnvironmentCrossplaneConfigUpdate
    }) => crossplaneApi.update(organizationUuid!, environmentUuid, config),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['crossplane-config', organizationUuid, variables.environmentUuid],
      })
    },
  })
}
