import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, ChevronDown, ChevronUp } from 'lucide-react'
import { applicationsApi, instancesApi, applicationComponentsApi, cronsApi, workersApi } from '../../services/api'
import type { ApplicationCreate, InstanceCreate, ApplicationComponentCreate } from '../../types'
import {
  ApplicationForm,
  InstanceForm,
  ComponentForm,
  InfoCard,
  type ComponentFormData,
  getDefaultWebappSettings,
  getDefaultCronSettings,
  getDefaultWorkerSettings,
} from '../../components/applications'
import { Breadcrumbs } from '../../components/Breadcrumbs'
import { PageHeader } from '../../components/PageHeader'

function CreateApplication() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  // Application form
  const [applicationData, setApplicationData] = useState<ApplicationCreate>({
    name: '',
    repository: '',
    enabled: true,
  })

  // Instance form
  const [instanceData, setInstanceData] = useState<Omit<InstanceCreate, 'application_uuid'>>({
    environment_uuid: '',
    image: '',
    version: '',
    enabled: true,
  })

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

  const createApplicationMutation = useMutation({
    mutationFn: applicationsApi.create,
  })

  const createInstanceMutation = useMutation({
    mutationFn: instancesApi.create,
  })

  const createComponentMutation = useMutation({
    mutationFn: applicationComponentsApi.create,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate application
    if (!applicationData.name) {
      setNotification({ type: 'error', message: 'Application name is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    // Validate instance
    if (!instanceData.environment_uuid || !instanceData.image || !instanceData.version) {
      setNotification({ type: 'error', message: 'Instance environment, image, and version are required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    // Validate components
    if (components.length === 0) {
      setNotification({ type: 'error', message: 'At least one component is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    for (const component of components) {
      if (!component.name || !component.settings) {
        setNotification({ type: 'error', message: 'All components must have name and settings' })
        setTimeout(() => setNotification(null), 5000)
        return
      }
      if (component.type === 'webapp') {
        const settings = component.settings as any
        const exposureType = settings?.exposure?.type || 'http'
        const exposureVisibility = settings?.exposure?.visibility || 'cluster'
        // URL is required only if exposure.type is 'http' AND visibility is not 'cluster'
        if (exposureType === 'http' && exposureVisibility !== 'cluster' && !component.url) {
          setNotification({ type: 'error', message: 'Webapp components with HTTP exposure type and visibility \'public\' or \'private\' must have a URL' })
          setTimeout(() => setNotification(null), 5000)
          return
        }
      }
      if (component.type === 'cron' && 'schedule' in component.settings && !component.settings.schedule) {
        setNotification({ type: 'error', message: 'Cron components must have a schedule' })
        setTimeout(() => setNotification(null), 5000)
        return
      }
    }

    setIsCreating(true)
    try {
      // Step 1: Create application
      const application = await createApplicationMutation.mutateAsync(applicationData)

      // Step 2: Create instance
      const instance = await createInstanceMutation.mutateAsync({
        ...instanceData,
        application_uuid: application.uuid,
      })

      // Step 3: Create components
      const componentPromises = components.map((component) => {
        if (component.type === 'cron') {
          const componentData: ApplicationComponentCreate = {
            instance_uuid: instance.uuid,
            name: component.name,
            type: 'cron',
            settings: component.settings,
            enabled: component.enabled,
          }
          return cronsApi.create(componentData)
        } else if (component.type === 'worker') {
          const componentData: ApplicationComponentCreate = {
            instance_uuid: instance.uuid,
            name: component.name,
            type: 'worker',
            settings: component.settings,
            enabled: component.enabled,
          }
          return workersApi.create(componentData)
        } else {
        const componentData: ApplicationComponentCreate = {
          instance_uuid: instance.uuid,
          name: component.name,
          type: 'webapp',
          settings: component.settings,
          visibility: component.visibility,
          url: component.url,
          enabled: component.enabled,
        }
        return createComponentMutation.mutateAsync(componentData)
        }
      })

      await Promise.all(componentPromises)

      setNotification({ type: 'success', message: 'Application, instance, and components created successfully!' })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['instances'] })
      queryClient.invalidateQueries({ queryKey: ['application-components'] })

      // Navigate to instance detail after 2 seconds
      setTimeout(() => {
        navigate(`/applications/${application.uuid}/instances/${instance.uuid}/components`)
      }, 2000)
    } catch (error: any) {
      setIsCreating(false)
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error creating application',
      })
      setTimeout(() => setNotification(null), 5000)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 relative">
      {isCreating && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-soft-lg p-8 flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <div className="text-center">
              <p className="text-lg font-semibold text-slate-800">Creating Application</p>
              <p className="text-sm text-slate-600 mt-1">Please wait while we create your application, instance, and components...</p>
            </div>
          </div>
        </div>
      )}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs
          items={[
            { label: 'Applications', path: '/applications' },
            { label: 'New Application' },
          ]}
        />

        {/* Header */}
        <div className="mb-8">
          <PageHeader title="Create New Application" description="Create a new application with instance and components in one step" />
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
          {/* Application Section */}
          <ApplicationForm data={applicationData} onChange={setApplicationData} />

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
              disabled={
                createApplicationMutation.isPending ||
                createInstanceMutation.isPending ||
                createComponentMutation.isPending
              }
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
            >
              {createApplicationMutation.isPending ||
              createInstanceMutation.isPending ||
              createComponentMutation.isPending
                ? 'Creating...'
                : 'Create Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateApplication

