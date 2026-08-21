import { X } from 'lucide-react'
import type { TemplateSettingDefinition, TemplateSettingType } from '../../features/templates'

interface TemplateSettingsEditorProps {
  settings: TemplateSettingDefinition[]
  onChange: (settings: TemplateSettingDefinition[]) => void
  slugPreview: string
}

export function TemplateSettingsEditor({ settings, onChange, slugPreview }: TemplateSettingsEditorProps) {
  const safeSettings = Array.isArray(settings) ? settings : []

  const addSetting = () => {
    onChange([...safeSettings, { name: '', description: '', type: 'string' }])
  }

  const updateSetting = (index: number, patch: Partial<TemplateSettingDefinition>) => {
    onChange(safeSettings.map((item, i) => (i === index ? { ...item, ...patch } : item)))
  }

  const removeSetting = (index: number) => {
    onChange(safeSettings.filter((_, i) => i !== index))
  }

  const jinjaPath = `application.template.${slugPreview || 'webapp_deployment'}.settings.<setting_name>`

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-sm font-semibold text-slate-700">Template settings</h5>
        <button
          type="button"
          onClick={addSetting}
          className="text-xs text-blue-600 hover:text-blue-700"
        >
          + Add
        </button>
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Values are set per component and available on all templates in the render as{' '}
        <code className="font-mono text-slate-700">{jinjaPath}</code>
        . Renaming a setting orphans existing component values.
      </p>
      {safeSettings.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-2">No template settings defined</p>
      ) : (
        <div className="space-y-2">
          {safeSettings.map((setting, index) => (
            <div key={index} className="flex items-start gap-2">
              <input
                type="text"
                value={setting.name}
                onChange={(e) => updateSetting(index, { name: e.target.value })}
                placeholder="name"
                className="flex-[2] px-2 py-1.5 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 font-mono"
              />
              <input
                type="text"
                value={setting.description || ''}
                onChange={(e) => updateSetting(index, { description: e.target.value })}
                placeholder="description"
                className="flex-[3] px-2 py-1.5 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
              />
              <select
                value={setting.type}
                onChange={(e) => updateSetting(index, { type: e.target.value as TemplateSettingType })}
                className="w-28 px-2 py-1.5 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 bg-white"
              >
                <option value="string">string</option>
                <option value="boolean">boolean</option>
              </select>
              <button
                type="button"
                onClick={() => removeSetting(index)}
                className="flex-shrink-0 p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors mt-0.5"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
