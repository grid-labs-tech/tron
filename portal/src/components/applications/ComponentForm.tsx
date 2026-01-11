import { X } from 'lucide-react'
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
}

export function ComponentForm({
  component,
  onChange,
  onRemove,
  showRemoveButton = true,
  title,
  isEditing = false,
  hasGatewayApi = true,
  gatewayResources = [],
  gatewayReference = { namespace: '', name: '' },
}: ComponentFormProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const updateField = (field: keyof ComponentFormData, value: any) => {
    onChange({ ...component, [field]: value })
  }

  const handleSettingsChange = (settings: WebappSettings | CronSettings | WorkerSettings) => {
    updateField('settings', settings)
  }

  // Se gateway_api não estiver disponível e visibility for public/private, forçar para cluster
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

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-800">{title || 'Component'}</h3>
        {showRemoveButton && onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <div className="space-y-4">
        {!isEditing && (
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Name *</label>
          <div className="flex items-center gap-4">
            <input
              type="text"
              value={component.name}
              onChange={(e) => {
                const value = e.target.value.replace(/\s/g, '')
                updateField('name', value)
              }}
              className="flex-1 px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
              placeholder="my-component"
              required
              pattern="[^\s]+"
              title="Component name cannot contain spaces"
            />
            <div className="flex items-center gap-4 whitespace-nowrap">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
                <input
                  type="radio"
                  name={`enabled-${component.name || 'component'}`}
                  checked={component.enabled === true}
                  onChange={() => updateField('enabled', true)}
                  className="border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                Enabled
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
                <input
                  type="radio"
                  name={`enabled-${component.name || 'component'}`}
                  checked={component.enabled === false}
                  onChange={() => updateField('enabled', false)}
                  className="border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                Disabled
              </label>
            </div>
          </div>
        </div>
        )}
        {isEditing && (
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Name</label>
            <div className="flex items-center gap-4">
              <div className="flex-1 px-2 py-1.5 border border-slate-200 rounded text-sm bg-slate-50 text-slate-600">
                {component.name}
              </div>
              <div className="flex items-center gap-4 whitespace-nowrap">
                <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
                  <input
                    type="radio"
                    name={`enabled-${component.name || 'component'}`}
                    checked={component.enabled === true}
                    onChange={() => updateField('enabled', true)}
                    className="border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  Enabled
                </label>
                <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
                  <input
                    type="radio"
                    name={`enabled-${component.name || 'component'}`}
                    checked={component.enabled === false}
                    onChange={() => updateField('enabled', false)}
                    className="border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  Disabled
                </label>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-1">Component name cannot be changed after creation</p>
          </div>
        )}

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
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}
