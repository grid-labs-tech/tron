import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useInstance } from '../../../features/instances'
import { useApplication } from '../../../features/applications'
import { useClusters } from '../../../features/clusters'
import { useUpdateInstance, useDeleteInstance, useSyncInstance } from '../../../features/instances'
import {
  useUpdateWebappComponent,
  useDeleteWebappComponent,
  useCreateWebappComponent,
  useUpdateCronComponent,
  useDeleteCronComponent,
  useCreateCronComponent,
  useUpdateWorkerComponent,
  useDeleteWorkerComponent,
  useCreateWorkerComponent,
} from '../../../features/components'
import type { InstanceComponent } from '../../../features/instances'

export const useInstanceDetail = (applicationUuid: string | undefined, instanceUuid: string | undefined) => {
  const navigate = useNavigate()

  const { data: instance, isLoading: isLoadingInstance } = useInstance(instanceUuid)
  const { data: application } = useApplication(applicationUuid)
  const { data: clusters } = useClusters()

  // Gateway API helpers
  const hasGatewayApi = useMemo(() => {
    if (!instance || !clusters || !instance.environment) return false
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instance.environment.uuid
    )
    return environmentClusters.some((cluster) => cluster.gateway?.api?.enabled === true)
  }, [instance, clusters])

  const gatewayResources = useMemo(() => {
    if (!instance || !clusters || !instance.environment) return []
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instance.environment.uuid
    )
    const allResources = new Set<string>()
    environmentClusters.forEach((cluster) => {
      if (cluster.gateway?.api?.enabled && cluster.gateway.api.resources) {
        cluster.gateway.api.resources.forEach((resource) => allResources.add(resource))
      }
    })
    return Array.from(allResources)
  }, [instance, clusters])

  const gatewayReference = useMemo(() => {
    if (!instance || !clusters || !instance.environment) return { namespace: '', name: '' }
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instance.environment.uuid
    )
    for (const cluster of environmentClusters) {
      if (cluster.gateway?.reference) {
        const namespace = cluster.gateway.reference.namespace || ''
        const name = cluster.gateway.reference.name || ''
        if (namespace && name) {
          return { namespace, name }
        }
      }
    }
    return { namespace: '', name: '' }
  }, [instance, clusters])

  // Components grouped by type
  const componentsByType = useMemo(() => {
    const grouped: Record<'webapp' | 'worker' | 'cron', InstanceComponent[]> = {
      webapp: [],
      worker: [],
      cron: [],
    }
    ;(instance?.components || []).forEach((component) => {
      const type = component.type as 'webapp' | 'worker' | 'cron'
      if (grouped[type]) {
        grouped[type].push(component)
      }
    })
    return grouped
  }, [instance?.components])

  // Mutations
  const updateInstanceMutation = useUpdateInstance()
  const deleteInstanceMutation = useDeleteInstance()
  const syncInstanceMutation = useSyncInstance()

  const updateWebappComponentMutation = useUpdateWebappComponent()
  const deleteWebappComponentMutation = useDeleteWebappComponent()
  const createWebappComponentMutation = useCreateWebappComponent()

  const updateCronComponentMutation = useUpdateCronComponent()
  const deleteCronComponentMutation = useDeleteCronComponent()
  const createCronComponentMutation = useCreateCronComponent()

  const updateWorkerComponentMutation = useUpdateWorkerComponent()
  const deleteWorkerComponentMutation = useDeleteWorkerComponent()
  const createWorkerComponentMutation = useCreateWorkerComponent()

  // Handle delete instance
  const handleDeleteInstance = () => {
    if (instanceUuid && confirm('Are you sure you want to delete this instance? This action cannot be undone.')) {
      deleteInstanceMutation.mutate(instanceUuid, {
        onSuccess: () => {
          navigate('/applications')
        },
      })
    }
  }

  // Handle sync instance
  const handleSyncInstance = () => {
    if (instanceUuid) {
      syncInstanceMutation.mutate(instanceUuid)
    }
  }

  // Handle delete component
  const handleDeleteComponent = (componentUuid: string, componentType: 'webapp' | 'worker' | 'cron') => {
    if (confirm('Are you sure you want to delete this component?')) {
      if (componentType === 'webapp') {
        deleteWebappComponentMutation.mutate(componentUuid)
      } else if (componentType === 'cron') {
        deleteCronComponentMutation.mutate(componentUuid)
      } else {
        deleteWorkerComponentMutation.mutate(componentUuid)
      }
    }
  }

  return {
    instance,
    application,
    isLoadingInstance,
    hasGatewayApi,
    gatewayResources,
    gatewayReference,
    componentsByType,
    updateInstanceMutation,
    deleteInstanceMutation,
    syncInstanceMutation,
    updateWebappComponentMutation,
    deleteWebappComponentMutation,
    createWebappComponentMutation,
    updateCronComponentMutation,
    deleteCronComponentMutation,
    createCronComponentMutation,
    updateWorkerComponentMutation,
    deleteWorkerComponentMutation,
    createWorkerComponentMutation,
    handleDeleteInstance,
    handleSyncInstance,
    handleDeleteComponent,
  }
}
