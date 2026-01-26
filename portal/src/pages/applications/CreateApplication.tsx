import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, ChevronDown, ChevronUp, Check, Circle } from 'lucide-react'
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
import { Breadcrumbs, PageHeader } from '../../shared/components'
import { useAuth } from '../../contexts/AuthContext'

type StepStatus = 'pending' | 'active' | 'completed'

interface StepHeaderProps {
  number: number
  title: string
  status: StepStatus
  summary?: string
  onClick?: () => void
  isClickable?: boolean
}

function StepHeader({ number, title, status, summary, onClick, isClickable }: StepHeaderProps) {
  const isActive = status === 'active'
  const isCompleted = status === 'completed'
  
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!isClickable}
      className={`w-full flex items-start gap-4 p-4 text-left transition-colors ${
        isClickable ? 'cursor-pointer hover:bg-slate-50' : 'cursor-default'
      } ${isActive ? 'bg-white' : ''}`}
    >
      {/* Step number/icon */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
        isCompleted 
          ? 'bg-blue-600 text-white' 
          : isActive 
            ? 'bg-blue-600 text-white'
            : 'bg-slate-200 text-slate-500'
      }`}>
        {isCompleted ? <Check size={16} /> : number}
      </div>
      
      {/* Step title and summary */}
      <div className="flex-1 min-w-0">
        <h3 className={`text-base font-semibold ${
          isActive ? 'text-slate-900' : isCompleted ? 'text-slate-700' : 'text-slate-400'
        }`}>
          {title}
        </h3>
        {isCompleted && summary && (
          <p className="text-sm text-slate-500 mt-0.5 truncate">{summary}</p>
        )}
        {!isActive && !isCompleted && (
          <p className="text-sm text-slate-400 mt-0.5">Complete the previous step to continue</p>
        )}
      </div>
      
      {/* Expand indicator */}
      {isClickable && (
        <div className="flex-shrink-0 text-slate-400">
          {isActive ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      )}
    </button>
  )
}

function CreateApplication() {
  const navigate = useNavigate()
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [, setErrors] = useState<Record<string, string>>({})
  const [isCreating, setIsCreating] = useState(false)
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  // Stepper state
  const [currentStep, setCurrentStep] = useState(1)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])

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

  // Check if any cluster in the selected environment has gateway_api available
  const hasGatewayApi = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return false
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instanceData.environment_uuid
    )
    return environmentClusters.some((cluster) => cluster.gateway?.api?.enabled === true)
  }, [instanceData.environment_uuid, clusters])

  // Get Gateway API resources available in clusters of the selected environment
  const gatewayResources = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return []
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instanceData.environment_uuid
    )
    const allResources = new Set<string>()
    environmentClusters.forEach((cluster) => {
      if (cluster.gateway?.api?.enabled && cluster.gateway.api.resources) {
        cluster.gateway.api.resources.forEach((resource) => allResources.add(resource))
      }
    })
    return Array.from(allResources)
  }, [instanceData.environment_uuid, clusters])

  // Get Gateway reference from clusters of the selected environment
  const gatewayReference = useMemo(() => {
    if (!instanceData.environment_uuid || !clusters) return { namespace: '', name: '' }
    const environmentClusters = clusters.filter(
      (cluster) => cluster.environment?.uuid === instanceData.environment_uuid
    )
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
  }, [instanceData.environment_uuid, clusters])

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

  // Step navigation
  const goToStep = (step: number) => {
    if (step < currentStep || completedSteps.includes(step - 1) || step === 1) {
      setCurrentStep(step)
    }
  }

  const continueToNextStep = () => {
    let isValid = false
    
    if (currentStep === 1) {
      isValid = validateStep1()
    } else if (currentStep === 2) {
      isValid = validateStep2()
    } else if (currentStep === 3) {
      isValid = validateStep3()
    }

    if (isValid) {
      if (!completedSteps.includes(currentStep)) {
        setCompletedSteps([...completedSteps, currentStep])
      }
      if (currentStep < 3) {
        setCurrentStep(currentStep + 1)
      }
    }
  }

  // Get step status
  const getStepStatus = (step: number): StepStatus => {
    if (currentStep === step) return 'active'
    if (completedSteps.includes(step)) return 'completed'
    return 'pending'
  }

  // Get step summary
  const getStepSummary = (step: number): string => {
    if (step === 1 && completedSteps.includes(1)) {
      return applicationData.name
    }
    if (step === 2 && completedSteps.includes(2)) {
      return `${instanceData.image}:${instanceData.version}`
    }
    if (step === 3 && completedSteps.includes(3)) {
      return `${components.length} component${components.length !== 1 ? 's' : ''}`
    }
    return ''
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
      
      // If application and instance were created, redirect anyway (partial success)
      if (application && instance) {
        setNotification({
          type: 'error',
          message: `Application created but there was an error with components: ${errorMessage}. Redirecting...`,
        })
        setTimeout(() => {
          navigate(`/applications/${application!.uuid}/instances/${instance!.uuid}/components`)
        }, 2000)
      } else if (application) {
        // Application created but instance failed
        setNotification({
          type: 'error',
          message: `Application created but instance failed: ${errorMessage}. Redirecting...`,
        })
        setTimeout(() => {
          navigate(`/applications/${application!.uuid}`)
        }, 2000)
      } else {
        // Complete failure - allow retry
        setIsCreating(false)
        setNotification({
          type: 'error',
          message: errorMessage,
        })
        setTimeout(() => setNotification(null), 5000)
      }
    }
  }

  const canSubmit = completedSteps.includes(1) && completedSteps.includes(2) && components.length > 0

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
            {notification.message}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Stepper Container */}
          <div className="bg-white rounded-xl shadow-soft border border-slate-200/60 overflow-hidden divide-y divide-slate-200">
            
            {/* Step 1: Application */}
            <div>
              <StepHeader
                number={1}
                title="Application"
                status={getStepStatus(1)}
                summary={getStepSummary(1)}
                onClick={() => goToStep(1)}
                isClickable={true}
              />
              {currentStep === 1 && (
                <div className="px-4 pb-6 pt-2 ml-12">
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
                  <div className="mt-6">
                    <button
                      type="button"
                      onClick={continueToNextStep}
                      className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      Continue
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Step 2: Instance */}
            <div>
              <StepHeader
                number={2}
                title="Instance"
                status={getStepStatus(2)}
                summary={getStepSummary(2)}
                onClick={() => goToStep(2)}
                isClickable={completedSteps.includes(1) || currentStep === 2}
              />
              {currentStep === 2 && (
                <div className="px-4 pb-6 pt-2 ml-12">
                  <InstanceForm data={instanceData} onChange={setInstanceData} showInfoCard={false} />
                  <div className="mt-6">
                    <button
                      type="button"
                      onClick={continueToNextStep}
                      className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      Continue
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Step 3: Components */}
            <div>
              <StepHeader
                number={3}
                title="Components"
                status={getStepStatus(3)}
                summary={getStepSummary(3)}
                onClick={() => goToStep(3)}
                isClickable={completedSteps.includes(2) || currentStep === 3}
              />
              {currentStep === 3 && (
                <div className="px-4 pb-6 pt-2 ml-12">
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
                </div>
              )}
            </div>
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
