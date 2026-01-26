import { X, Globe, Clock, Cpu } from 'lucide-react'
import { useEffect } from 'react'
import type { ComponentFormData, WebappSettings, CronSettings, WorkerSettings } from './types'
import { WebappForm } from './WebappForm'
import { CronForm } from './CronForm'
import { WorkerForm } from './WorkerForm'

interface ComponentFormProps {
  component: ComponentFormData
  onChange: (component: ComponentFormData) => void
  onRemove?: () => void
  showRemoveButton?: boolean
  title?: string
  isEditing?: boolean
  hasGatewayApi?: boolean
  gatewayResources?: string[]
  gatewayReference?: { namespace: string; name: string }
  isAdmin?: boolean
  componentUuid?: string
  hasEnvironmentSelected?: boolean
}

const typeIcons = {
  webapp: Globe,
  cron: Clock,
  worker: Cpu,
}

const typeColors = {
  webapp: 'text-slate-700 bg-emerald-50 border-emerald-200',
  cron: 'text-slate-700 bg-orange-50 border-orange-200',
  worker: 'text-slate-700 bg-purple-50 border-purple-200',
}

const iconColors = {
  webapp: 'text-emerald-600',
  cron: 'text-orange-600',
  worker: 'text-purple-600',
}

export function ComponentForm({
  component,
  onChange,
  onRemove,
  showRemoveButton = true,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  title: _title,
  isEditing = false,
  hasGatewayApi = true,
  gatewayResources = [],
  gatewayReference = { namespace: '', name: '' },
  isAdmin = false,
  componentUuid,
  hasEnvironmentSelected = true,
}: ComponentFormProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const updateField = (field: keyof ComponentFormData, value: any) => {
    onChange({ ...component, [field]: value })
  }

  const handleSettingsChange = (settings: WebappSettings | CronSettings | WorkerSettings) => {
    updateField('settings', settings)
  }

  // If gateway_api is not available and visibility is public/private, force to cluster
  useEffect(() => {
    if (component.type === 'webapp' && !hasGatewayApi) {
      const settings = component.settings as WebappSettings | null
      if (settings && 'exposure' in settings) {
        const exposureVisibility = settings.exposure.visibility
        if (exposureVisibility === 'public' || exposureVisibility === 'private') {
          onChange({
            ...component,
            visibility: 'cluster',
            settings: {
              ...settings,
              exposure: { ...settings.exposure, visibility: 'cluster' },
            },
          })
        }
      } else if (component.visibility === 'public' || component.visibility === 'private') {
        onChange({ ...component, visibility: 'cluster' })
      }
    }
  }, [hasGatewayApi]) // eslint-disable-line react-hooks/exhaustive-deps

  const TypeIcon = typeIcons[component.type]

  return (
    <div className={`border rounded-lg overflow-hidden bg-white ${typeColors[component.type]}`}>
      {/* Compact Header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 border-b border-slate-200">
        <div className={`p-1.5 rounded ${typeColors[component.type]}`}>
          <TypeIcon size={16} className={iconColors[component.type]} />
        </div>
        
        {/* Name Input or Display */}
        {!isEditing ? (
          <input
            type="text"
            value={component.name}
            onChange={(e) => {
              const value = e.target.value.replace(/\s/g, '')
              updateField('name', value)
            }}
            className="flex-1 px-2 py-1 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 bg-white"
            placeholder={`my-${component.type}`}
            required
            pattern="[^\s]+"
            title="Component name cannot contain spaces"
          />
        ) : (
          <span className="flex-1 text-sm font-medium text-slate-700">{component.name}</span>
        )}

        {/* Enabled Toggle */}
        <div className="flex items-center gap-2">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={component.enabled}
              onChange={(e) => updateField('enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
          <span className="text-xs text-slate-500">{component.enabled ? 'On' : 'Off'}</span>
        </div>

        {/* Remove Button */}
        {showRemoveButton && onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            title="Remove component"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Component Settings */}
      <div className="px-4 py-3">
        {component.type === 'webapp' && (
          <>
            {component.settings && ('exposure' in component.settings || 'endpoints' in component.settings) && (
              <WebappForm
                settings={component.settings as WebappSettings}
                onChange={handleSettingsChange as (settings: WebappSettings) => void}
                url={component.url}
                onUrlChange={(url) => updateField('url', url)}
                hasGatewayApi={hasGatewayApi}
                gatewayResources={gatewayResources}
                gatewayReference={gatewayReference}
                isAdmin={isAdmin}
                componentUuid={componentUuid}
                hasEnvironmentSelected={hasEnvironmentSelected}
              />
            )}
          </>
        )}

        {component.type === 'cron' && (
          <>
            {component.settings && 'schedule' in component.settings && (
              <CronForm
                settings={component.settings as CronSettings}
                onChange={handleSettingsChange as (settings: CronSettings) => void}
                isAdmin={isAdmin}
                componentUuid={componentUuid}
              />
            )}
          </>
        )}

        {component.type === 'worker' && (
          <>
            {component.settings && 'custom_metrics' in component.settings && (
              <WorkerForm
                settings={component.settings as WorkerSettings}
                onChange={handleSettingsChange as (settings: WorkerSettings) => void}
                isAdmin={isAdmin}
                componentUuid={componentUuid}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}
