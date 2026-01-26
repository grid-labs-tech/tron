import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, ChevronDown, ChevronUp, Circle } from 'lucide-react'
import { useCreateApplication } from '../../features/applications'
import { useClusters } from '../../features/clusters'
import { useCreateInstance } from '../../features/instances'
import { useCreateWebappComponent, useCreateCronComponent, useCreateWorkerComponent } from '../../features/components'
import { applicationCreateSchema } from '../../features/applications/schemas'
import { instanceFormSchema } from '../../features/instances/schemas'
import { componentCreateSchema } from '../../features/components/schemas'
import { validateForm } from '../../shared/utils/validation'
import type { ApplicationCreate } from '../../features/applications'
import type { InstanceCreate } from '../../features/instances'
import {
  InstanceForm,
  ComponentForm,
  type ComponentFormData,
  getDefaultWebappSettings,
  getDefaultCronSettings,
  getDefaultWorkerSettings,
} from '../../components/applications'
import { Breadcrumbs, PageHeader, Stepper, useStepper, type Step } from '../../shared/components'
import { useAuth } from '../../contexts/AuthContext'

function CreateApplication() {
  const navigate = useNavigate()
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [, setErrors] = useState<Record<string, string>>({})
  const [isCreating, setIsCreating] = useState(false)
  const [partialSuccess, setPartialSuccess] = useState<{ applicationUuid: string; instanceUuid: string } | null>(null)
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  // Stepper state
  const { currentStep, completedSteps, goToStep, completeStep } = useStepper(1)

  const createApplicationMutation = useCreateApplication()
  const { data: clusters } = useClusters()
  const createInstanceMutation = useCreateInstance()
  const createWebappComponentMutation = useCreateWebappComponent()
  const createCronComponentMutation = useCreateCronComponent()
  const createWorkerComponentMutation = useCreateWorkerComponent()

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

  // Check if environment has any clusters
  const environmentClusters = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return []
    return clusters.filter(
      (cluster) => cluster.environment?.uuid === instanceData.environment_uuid
    )
  }, [instanceData.environment_uuid, clusters])

  const hasNoClusters = instanceData.environment_uuid && environmentClusters.length === 0

  // Check if any cluster in the selected environment has gateway_api available
  const hasGatewayApi = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return false
    return environmentClusters.some((cluster) => cluster.gateway?.api?.enabled === true)
  }, [instanceData.environment_uuid, clusters, environmentClusters])

  // Get Gateway API resources available in clusters of the selected environment
  const gatewayResources = useMemo(() => {
    if (environmentClusters.length === 0) return []
    const allResources = new Set<string>()
    environmentClusters.forEach((cluster) => {
      if (cluster.gateway?.api?.enabled && cluster.gateway.api.resources) {
        cluster.gateway.api.resources.forEach((resource) => allResources.add(resource))
      }
    })
    return Array.from(allResources)
  }, [environmentClusters])

  // Get Gateway reference from clusters of the selected environment
  const gatewayReference = useMemo(() => {
    if (environmentClusters.length === 0) return { namespace: '', name: '' }
    for (const cluster of environmentClusters) {
      if (cluster.gateway?.reference) {
        const ref = cluster.gateway.reference.private || cluster.gateway.reference.public || { namespace: '', name: '' }
        const namespace = ref.namespace || ''
        const name = ref.name || ''
        if (namespace && name) {
          return { namespace, name }
        }
      }
    }
    return { namespace: '', name: '' }
  }, [environmentClusters])

  // Components
  const [components, setComponents] = useState<ComponentFormData[]>([])
  const [isComponentTypeDropdownOpen, setIsComponentTypeDropdownOpen] = useState(false)

  const addComponent = (type: 'webapp' | 'worker' | 'cron' = 'webapp') => {
    const defaultSettings = type === 'webapp' 
      ? getDefaultWebappSettings() 
      : type === 'cron' 
        ? getDefaultCronSettings() 
        : getDefaultWorkerSettings()
    
    setComponents([
      ...components,
      {
        name: '',
        type,
        url: null,
        visibility: 'private',
        enabled: true,
        settings: defaultSettings,
      },
    ])
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

  // Step validation functions
  const validateStep1 = () => {
    const validation = validateForm(applicationCreateSchema, applicationData)
    if (!validation.success) {
      setNotification({ type: 'error', message: 'Please fill in all required fields' })
      setTimeout(() => setNotification(null), 3000)
      return false
    }
    return true
  }

  const validateStep2 = () => {
    const validation = validateForm(instanceFormSchema, instanceData)
    if (!validation.success) {
      setNotification({ type: 'error', message: 'Please fill in all required fields' })
      setTimeout(() => setNotification(null), 3000)
      return false
    }
    return true
  }

  const validateStep3 = () => {
    if (components.length === 0) {
      setNotification({ type: 'error', message: 'At least one component is required' })
      setTimeout(() => setNotification(null), 3000)
      return false
    }
    for (let i = 0; i < components.length; i++) {
      const componentValidation = validateForm(componentCreateSchema, components[i])
      if (!componentValidation.success) {
        setNotification({
          type: 'error',
          message: `Component ${i + 1}: Please fill in all required fields`
        })
        setTimeout(() => setNotification(null), 3000)
        return false
      }
    }
    return true
  }

  // Validate envs and secrets for empty values
  const validateEnvsAndSecrets = (): string | null => {
    for (const component of components) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const settings = component.settings as any
      if (!settings) continue

      // Check envs
      if (settings.envs && Array.isArray(settings.envs)) {
        for (const env of settings.envs) {
          if (!env.key?.trim() && !env.value?.trim()) continue // Skip completely empty rows
          if (!env.key?.trim()) {
            return `Component "${component.name}": Environment variable is missing a key`
          }
          if (!env.value?.trim()) {
            return `Component "${component.name}": Environment variable "${env.key}" is missing a value`
          }
        }
      }

      // Check secrets
      if (settings.secrets && Array.isArray(settings.secrets)) {
        for (const secret of settings.secrets) {
          if (secret.value === '********') continue // Skip masked values
          if (!secret.key?.trim() && !secret.value?.trim()) continue // Skip completely empty rows
          if (!secret.key?.trim()) {
            return `Component "${component.name}": Secret is missing a key`
          }
          if (!secret.value?.trim()) {
            return `Component "${component.name}": Secret "${secret.key}" is missing a value`
          }
        }
      }
    }
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setNotification(null)
    setErrors({})

    // Validate all steps
    if (!validateStep1() || !validateStep2() || !validateStep3()) {
      return
    }

    // Validate envs and secrets
    const envsSecretsError = validateEnvsAndSecrets()
    if (envsSecretsError) {
      setNotification({ type: 'error', message: envsSecretsError })
      return
    }

    // Check if environment has clusters
    if (hasNoClusters) {
      setNotification({
        type: 'error',
        message: 'The selected environment has no clusters. Please add a cluster in Settings → Clusters before creating components.',
      })
      return
    }

    setIsCreating(true)
    
    let application: { uuid: string } | null = null
    let instance: { uuid: string } | null = null
    
    try {
      // Step 1: Create application
      application = await createApplicationMutation.mutateAsync(applicationData)

      // Step 2: Create instance
      instance = await createInstanceMutation.mutateAsync({
        ...instanceData,
        application_uuid: application.uuid,
      })

      // Step 3: Create components
      const componentPromises = components.map((component) => {
        // Filter out completely empty rows (both key and value empty)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let cleanedSettings = component.settings as any
        if (cleanedSettings) {
          if (cleanedSettings.envs && Array.isArray(cleanedSettings.envs)) {
            cleanedSettings = {
              ...cleanedSettings,
              envs: cleanedSettings.envs.filter(
                (env: { key: string; value: string }) => env.key?.trim() || env.value?.trim()
              ),
            }
          }
          if (cleanedSettings.secrets && Array.isArray(cleanedSettings.secrets)) {
            cleanedSettings = {
              ...cleanedSettings,
              secrets: cleanedSettings.secrets.filter(
                (secret: { key: string; value: string }) => 
                  secret.value === '********' || secret.key?.trim() || secret.value?.trim()
              ),
            }
          }
        }

        const componentData = {
          instance_uuid: instance!.uuid,
          name: component.name,
          type: component.type,
          settings: cleanedSettings,
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

      setNotification({ type: 'success', message: 'Application created successfully!' })

      setTimeout(() => {
        navigate(`/applications/${application!.uuid}/instances/${instance!.uuid}/components`)
      }, 1500)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Error creating application'
      setIsCreating(false)
      
      // If application and instance were created, show error but allow user to decide
      if (application && instance) {
        setPartialSuccess({ applicationUuid: application.uuid, instanceUuid: instance.uuid })
        setNotification({
          type: 'error',
          message: `Application and instance created, but component failed: ${errorMessage}`,
        })
        // Show a button to navigate or let user fix the issue and retry
        // Don't auto-redirect - let user see the error and decide
      } else if (application) {
        // Application created but instance failed
        setNotification({
          type: 'error',
          message: `Application created but instance failed: ${errorMessage}`,
        })
      } else {
        // Complete failure - allow retry
        setNotification({
          type: 'error',
          message: errorMessage,
        })
      }
      // Don't auto-hide error notifications - let user dismiss them
    }
  }

  const canSubmit = completedSteps.includes(1) && completedSteps.includes(2) && components.length > 0

  // Step content components
  const step1Content = (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Application Name *</label>
        <input
          type="text"
          value={applicationData.name}
          onChange={(e) => setApplicationData({ ...applicationData, name: e.target.value.replace(/\s/g, '') })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
          placeholder="my-application"
          required
        />
        <p className="text-xs text-slate-500 mt-1">A unique name for your application (no spaces)</p>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Repository (optional)</label>
        <input
          type="text"
          value={applicationData.repository || ''}
          onChange={(e) => setApplicationData({ ...applicationData, repository: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
          placeholder="https://github.com/org/repo"
        />
        <p className="text-xs text-slate-500 mt-1">Link to the source code repository</p>
      </div>
    </div>
  )

  const step2Content = (
    <div className="space-y-4">
      <InstanceForm data={instanceData} onChange={setInstanceData} showInfoCard={false} />
      {hasNoClusters && (
        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-800">
          <div className="flex items-start gap-2">
            <span className="text-amber-500 mt-0.5">⚠️</span>
            <div>
              <p className="font-medium">No clusters in this environment</p>
              <p className="text-sm mt-1">
                This environment has no clusters configured. You won't be able to deploy components until a cluster is added.
                Go to <span className="font-medium">Settings → Clusters</span> to add one.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const step3Content = (
    <>
      {/* Add Component Button */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-600">Add at least one component to your application.</p>
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsComponentTypeDropdownOpen(!isComponentTypeDropdownOpen)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-soft hover:shadow-soft-lg transition-all duration-200 text-sm font-medium"
          >
            <Plus size={18} />
            <span>Add Component</span>
            {isComponentTypeDropdownOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
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
                  className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 first:rounded-t-lg transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Circle size={8} className="text-green-500 fill-green-500" />
                    <span>Webapp</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 ml-4">HTTP/HTTPS service</p>
                </button>
                <button
                  type="button"
                  onClick={() => addComponent('worker')}
                  className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Circle size={8} className="text-purple-500 fill-purple-500" />
                    <span>Worker</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 ml-4">Background process</p>
                </button>
                <button
                  type="button"
                  onClick={() => addComponent('cron')}
                  className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 last:rounded-b-lg transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Circle size={8} className="text-orange-500 fill-orange-500" />
                    <span>Cron</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 ml-4">Scheduled job</p>
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Components List */}
      {components.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
          <div className="text-slate-400 mb-2">
            <Plus size={32} className="mx-auto" />
          </div>
          <p className="text-slate-500">No components added yet</p>
          <p className="text-sm text-slate-400 mt-1">Click "Add Component" to get started</p>
        </div>
      ) : (
        <div className="space-y-4">
          {components.map((component, index) => (
            <ComponentForm
              key={index}
              component={component}
              onChange={(updatedComponent) => updateComponent(index, updatedComponent)}
              onRemove={() => removeComponent(index)}
              hasGatewayApi={hasGatewayApi}
              gatewayResources={gatewayResources}
              gatewayReference={gatewayReference}
              isAdmin={isAdmin}
              title={`Component ${index + 1}: ${component.type.charAt(0).toUpperCase() + component.type.slice(1)}`}
              hasEnvironmentSelected={!!instanceData.environment_uuid}
            />
          ))}
        </div>
      )}
    </>
  )

  // Steps configuration
  const steps: Step[] = [
    {
      id: 1,
      title: 'Application',
      summary: completedSteps.includes(1) ? applicationData.name : undefined,
      content: step1Content,
      validate: validateStep1,
    },
    {
      id: 2,
      title: 'Instance',
      summary: completedSteps.includes(2) ? `${instanceData.image}:${instanceData.version}` : undefined,
      content: step2Content,
      validate: validateStep2,
    },
    {
      id: 3,
      title: 'Components',
      summary: completedSteps.includes(3) ? `${components.length} component${components.length !== 1 ? 's' : ''}` : undefined,
      content: step3Content,
      validate: validateStep3,
    },
  ]

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
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs
          items={[
            { label: 'Applications', path: '/applications' },
            { label: 'New Application' },
          ]}
        />

        {/* Header */}
        <div className="mb-8">
          <PageHeader title="Create New Application" description="Follow the steps below to create your application" />
        </div>

        {/* Notification */}
        {notification && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              notification.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between">
                <span>{notification.message}</span>
                <button
                  type="button"
                  onClick={() => {
                    setNotification(null)
                    if (!partialSuccess) setPartialSuccess(null)
                  }}
                  className="text-slate-400 hover:text-slate-600 ml-2"
                >
                  ✕
                </button>
              </div>
              {partialSuccess && notification.type === 'error' && (
                <div className="flex gap-2 mt-2">
                  <button
                    type="button"
                    onClick={() => navigate(`/applications/${partialSuccess.applicationUuid}/instances/${partialSuccess.instanceUuid}/components`)}
                    className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    Go to Instance (add components there)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setNotification(null)
                      setPartialSuccess(null)
                    }}
                    className="px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                  >
                    Stay and fix
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Stepper Container */}
          <div className="bg-white rounded-xl shadow-soft border border-slate-200/60 overflow-hidden divide-y divide-slate-200">
            <Stepper
              steps={steps}
              currentStep={currentStep}
              completedSteps={completedSteps}
              onStepChange={goToStep}
              onStepComplete={completeStep}
              showContinueButton={currentStep < 3}
            />
          </div>

          {/* Submit Button - Always visible at bottom */}
          <div className="flex justify-between items-center mt-6 pt-6 border-t border-slate-200">
            <button
              type="button"
              onClick={() => navigate('/applications')}
              className="px-6 py-2.5 text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit || isCreating}
              className={`px-6 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                canSubmit && !isCreating
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-soft'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              }`}
            >
              {isCreating ? 'Creating...' : 'Create Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateApplication
