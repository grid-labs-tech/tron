import type { TemplateSettingsGroup } from '../../../features/templates'

export type TemplateSettingValues = Record<string, Record<string, boolean | string>>

interface TemplateSettingsInputProps {
  groups: TemplateSettingsGroup[]
  values: TemplateSettingValues
  onChange: (values: TemplateSettingValues) => void
}

export function TemplateSettingsInput({ groups, values, onChange }: TemplateSettingsInputProps) {
  const safeGroups = Array.isArray(groups) ? groups : []
  const safeValues = values && typeof values === 'object' ? values : {}

  const updateValue = (slug: string, name: string, value: boolean | string) => {
    onChange({
      ...safeValues,
      [slug]: {
        ...(safeValues[slug] || {}),
        [name]: value,
      },
    })
  }

  if (safeGroups.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      {safeGroups.map((group) => (
        <div key={group.template_uuid} className="border border-slate-200 rounded-lg p-3 bg-white">
          <h5 className="text-xs font-semibold text-slate-700 mb-2">{group.template_name}</h5>
          <div className="space-y-2">
            {group.settings.map((setting) => {
              const current = safeValues[group.template_slug]?.[setting.name]
              const label = setting.description || setting.name
              if (setting.type === 'boolean') {
                return (
                  <label key={setting.name} className="flex items-center gap-2 text-xs font-medium text-slate-600">
                    <input
                      type="checkbox"
                      checked={current === true}
                      onChange={(e) => updateValue(group.template_slug, setting.name, e.target.checked)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    {label}
                  </label>
                )
              }
              return (
                <div key={setting.name}>
                  <label className="block text-xs font-medium text-slate-600 mb-1">{label}</label>
                  <input
                    type="text"
                    value={typeof current === 'string' ? current : ''}
                    onChange={(e) => updateValue(group.template_slug, setting.name, e.target.value)}
                    className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
                  />
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
