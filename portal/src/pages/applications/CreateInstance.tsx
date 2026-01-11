import { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Plus, ChevronDown, ChevronUp } from 'lucide-react'
import { useApplication } from '../../features/applications'
import { useClusters } from '../../features/clusters'
import { useCreateInstance } from '../../features/instances'
import { useCreateWebappComponent, useCreateCronComponent, useCreateWorkerComponent } from '../../features/components'
import { instanceCreateSchema } from '../../features/instances/schemas'
import { componentCreateSchema } from '../../features/components/schemas'
import { validateForm } from '../../shared/utils/validation'
import type { InstanceCreate } from '../../features/instances'
import {
  InstanceForm,
  ComponentForm,
  InfoCard,
  type ComponentFormData,
  getDefaultWebappSettings,
  getDefaultCronSettings,
  getDefaultWorkerSettings,
} from '../../components/applications'
import { Breadcrumbs, PageHeader } from '../../shared/components'

function CreateInstance() {
  const { uuid: applicationUuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { data: application } = useApplication(applicationUuid)
  const { data: clusters } = useClusters()
  const createInstanceMutation = useCreateInstance()
  const createWebappComponentMutation = useCreateWebappComponent()
  const createCronComponentMutation = useCreateCronComponent()
  const createWorkerComponentMutation = useCreateWorkerComponent()

  // Instance form
  const [instanceData, setInstanceData] = useState<Omit<InstanceCreate, 'application_uuid'>>({
    environment_uuid: '',
    image: '',
    version: '',
    enabled: true,
  })

  // Verificar se algum cluster do environment selecionado tem gateway_api disponível
  const hasGatewayApi = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return false
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instanceData.environment_uuid
    )
    return environmentClusters.some((cluster) => cluster.gateway?.api?.enabled === true)
  }, [instanceData.environment_uuid, clusters])

  // Obter recursos do Gateway API disponíveis nos clusters do environment selecionado
  const gatewayResources = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return []
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instanceData.environment_uuid
    )
    // Pegar recursos de todos os clusters que têm Gateway API habilitado
    const allResources = new Set<string>()
    environmentClusters.forEach((cluster) => {
      if (cluster.gateway?.api?.enabled && cluster.gateway.api.resources) {
        cluster.gateway.api.resources.forEach((resource) => allResources.add(resource))
      }
    })
    return Array.from(allResources)
  }, [instanceData.environment_uuid, clusters])

  // Obter referência do Gateway (namespace e name) dos clusters do environment selecionado
  const gatewayReference = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return { namespace: '', name: '' }
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instanceData.environment_uuid
    )
    // Pegar o primeiro gateway reference encontrado que tenha namespace e name preenchidos
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
  }, [instanceData.environment_uuid, clusters])

  // Components
  const [components, setComponents] = useState<ComponentFormData[]>([])
  const [isComponentTypeDropdownOpen, setIsComponentTypeDropdownOpen] = useState(false)

  const addComponent = (type: 'webapp' | 'worker' | 'cron' = 'webapp') => {
    if (type === 'webapp') {
      setComponents([
        ...components,
        {
          name: '',
          type: 'webapp',
          url: null,
          visibility: 'private',
          enabled: true,
          settings: getDefaultWebappSettings(),
        },
      ])
    } else if (type === 'cron') {
      setComponents([
        ...components,
        {
          name: '',
          type: 'cron',
          url: null,
          visibility: 'private',
          enabled: true,
          settings: getDefaultCronSettings(),
        },
      ])
    } else {
      setComponents([
        ...components,
        {
          name: '',
          type: 'worker',
          url: null,
          visibility: 'private',
          enabled: true,
          settings: getDefaultWorkerSettings(),
        },
      ])
    }
    setIsComponentTypeDropdownOpen(false)
  }

  const removeComponent = (index: number) => {
    setComponents(components.filter((_, i) => i !== index))
  }

  const updateComponent = (index: number, component: ComponentFormData) => {
    const updated = [...components]
    updated[index] = component
    setComponents(updated)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setNotification(null)
    setErrors({})

    if (!applicationUuid) {
      setNotification({ type: 'error', message: 'Application UUID is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    // Validate instance
    const instanceValidation = validateForm(instanceCreateSchema, {
      ...instanceData,
      application_uuid: applicationUuid,
    })
    if (!instanceValidation.success) {
      setErrors(instanceValidation.errors || {})
      setNotification({ type: 'error', message: 'Please fix instance form errors' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    // Validate components
    for (let i = 0; i < components.length; i++) {
      const component = components[i]
      const componentValidation = validateForm(componentCreateSchema, component)
      if (!componentValidation.success) {
        setNotification({
          type: 'error',
          message: `Component ${i + 1}: ${Object.values(componentValidation.errors || {}).join(', ')}`
        })
        setTimeout(() => setNotification(null), 5000)
        return
      }
    }

    try {
      // Step 1: Create instance
      const instance = await createInstanceMutation.mutateAsync({
        ...instanceData,
        application_uuid: applicationUuid,
      })

      // Step 2: Create components
      if (components.length > 0) {
        const componentPromises = components.map((component) => {
          const componentData = {
            instance_uuid: instance.uuid,
            name: component.name,
            type: component.type,
            settings: component.settings,
            visibility: component.visibility,
            url: component.url,
            enabled: component.enabled,
          }

          if (component.type === 'cron') {
            return createCronComponentMutation.mutateAsync(componentData)
          } else if (component.type === 'worker') {
            return createWorkerComponentMutation.mutateAsync(componentData)
          } else {
            return createWebappComponentMutation.mutateAsync(componentData)
          }
        })

        await Promise.all(componentPromises)
      }

      setNotification({ type: 'success', message: 'Instance and components created successfully!' })

      // Navigate to instance detail page
      navigate(`/applications/${applicationUuid}/instances/${instance.uuid}/components`)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error creating instance',
      })
      setTimeout(() => setNotification(null), 5000)
    }
  }

  if (!application) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-slate-600 mb-4">Loading application...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs
          items={[
            { label: 'Applications', path: '/applications' },
            { label: application.name },
            { label: 'New Instance' },
          ]}
        />

        {/* Header */}
        <div className="mb-8">
          <PageHeader
            title="Create New Instance"
            description={`Create a new instance for ${application.name} with components`}
          />
        </div>

        {/* Notification */}
        {notification && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              notification.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
            }`}
          >
            {notification.message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Instance Section */}
          <InstanceForm data={instanceData} onChange={setInstanceData} />

          {/* Components Section */}
          <div className="bg-white rounded-xl shadow-soft border border-slate-200/60 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-800">Components</h2>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setIsComponentTypeDropdownOpen(!isComponentTypeDropdownOpen)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-soft hover:shadow-soft-lg transition-all duration-200 text-sm font-medium"
                >
                  <Plus size={18} />
                  <span>Add Component</span>
                  {isComponentTypeDropdownOpen ? (
                    <ChevronUp size={16} />
                  ) : (
                    <ChevronDown size={16} />
                  )}
                </button>
                {isComponentTypeDropdownOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setIsComponentTypeDropdownOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 z-20">
                      <button
                        type="button"
                        onClick={() => addComponent('webapp')}
                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 first:rounded-t-lg last:rounded-b-lg transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Plus size={16} />
                          <span>Webapp</span>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => addComponent('cron')}
                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 first:rounded-t-lg last:rounded-b-lg transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Plus size={16} />
                          <span>Cron</span>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => addComponent('worker')}
                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 first:rounded-t-lg last:rounded-b-lg transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Plus size={16} />
                          <span>Worker</span>
                        </div>
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Info Card */}
            <InfoCard>
              <p className="text-sm text-blue-900 leading-relaxed mb-2">
                Components are the building blocks of your application instance. Each component represents a specific service or workload that runs within the same container image and version. Available component types:
              </p>
              <ul className="text-sm text-blue-900 space-y-1.5 ml-4 list-disc">
                <li>
                  <strong>Webapp:</strong> A web application component that serves HTTP/HTTPS traffic. Requires a URL and can be configured with endpoints, healthchecks, environment variables, command override, and resource limits (CPU, memory).
                </li>
                <li>
                  <strong>Worker:</strong> A background worker component that processes jobs or tasks asynchronously. Typically used for long-running background processes, queue processing, or scheduled tasks.
                </li>
                <li>
                  <strong>Cron:</strong> A scheduled job component that runs at specified intervals using cron syntax. Ideal for periodic maintenance tasks, data synchronization, or scheduled reports.
                </li>
              </ul>
            </InfoCard>

            {components.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <p>No components added yet. Click "Add Component" to get started.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {components.map((component, index) => (
                  <ComponentForm
                    key={index}
                    component={component}
                    onChange={(updatedComponent) => updateComponent(index, updatedComponent)}
                    onRemove={() => removeComponent(index)}
                    hasGatewayApi={hasGatewayApi}
                    gatewayResources={gatewayResources}
                    gatewayReference={gatewayReference}
                    title={`Component ${index + 1}`}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => navigate('/applications')}
              className="px-6 py-2.5 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createInstanceMutation.isPending}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
            >
              {createInstanceMutation.isPending
                ? 'Creating...'
                : 'Create Instance'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateInstance

