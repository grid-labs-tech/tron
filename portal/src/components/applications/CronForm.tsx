import { useState } from 'react'
import { ChevronDown, ChevronRight, Settings2, FileCode } from 'lucide-react'
import type { CronSettings } from './types'
import type { EnvironmentSettingsLimits } from '../../features/environments'
import { CpuMemoryInput } from './form-components/CpuMemoryInput'
import { ScheduleInput } from './form-components/ScheduleInput'
import { EnvVarsInput } from './form-components/EnvVarsInput'
import { SecretsInput } from './form-components/SecretsInput'
import { CommandInput } from './form-components/CommandInput'
import { TemplateSettingsInput } from './form-components/TemplateSettingsInput'
import { useTemplateSettingsForComponent } from '../../features/templates'

interface CronFormProps {
  settings: CronSettings
  onChange: (settings: CronSettings) => void
  isAdmin?: boolean
  organizationUuid?: string
  componentUuid?: string
  envLimits?: EnvironmentSettingsLimits
}

export function CronForm({ settings, onChange, isAdmin = false, organizationUuid, componentUuid, envLimits }: CronFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showTemplateSettings, setShowTemplateSettings] = useState(false)
  const { data: templateSettingGroups = [] } = useTemplateSettingsForComponent(organizationUuid, 'cron')
  
  const updateField = <K extends keyof CronSettings>(field: K, value: CronSettings[K]) => {
    onChange({ ...settings, [field]: value })
  }

  // Check if any advanced settings have been modified from defaults
  const hasAdvancedChanges = () => {
    const hasEnvs = settings.envs && settings.envs.length > 0
    const hasSecrets = settings.secrets && settings.secrets.length > 0
    const hasCustomCpu = settings.cpu !== undefined && settings.cpu !== 0.5
    const hasCustomMemory = settings.memory !== undefined && settings.memory !== 512
    return hasEnvs || hasSecrets || hasCustomCpu || hasCustomMemory
  }

  const hasTemplateSettingsValues = Object.values(settings.template_settings || {}).some(
    (group) => group && Object.keys(group).length > 0
  )

  return (
    <div className="mt-3 space-y-3">
      {/* Essential Settings */}
      <ScheduleInput
        schedule={settings.schedule}
        onChange={(schedule) => updateField('schedule', schedule)}
      />

      <CommandInput
        command={settings.command}
        onChange={(command) => updateField('command', command)}
      />

      {/* Advanced Settings Toggle */}
      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors py-1"
      >
        {showAdvanced ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <Settings2 size={14} />
        <span className="font-medium">Advanced Settings</span>
        {hasAdvancedChanges() && !showAdvanced && (
          <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">Modified</span>
        )}
      </button>

      {/* Advanced Settings Content */}
      {showAdvanced && (
        <div className="space-y-3 pl-4 border-l-2 border-slate-200">
          <CpuMemoryInput
            cpu={settings.cpu}
            memory={settings.memory}
            onCpuChange={(cpu) => updateField('cpu', cpu)}
            onMemoryChange={(memory) => updateField('memory', memory)}
            minCpu={envLimits?.minCpuCores}
            maxCpu={envLimits?.maxCpuCores}
            minMemory={envLimits?.minMemoryMegabytes}
            maxMemory={envLimits?.maxMemoryMegabytes}
          />

          <EnvVarsInput
            envs={settings.envs}
            onChange={(envs) => updateField('envs', envs)}
          />

          <SecretsInput
            secrets={settings.secrets || []}
            onChange={(secrets) => updateField('secrets', secrets)}
            isAdmin={isAdmin}
            organizationUuid={organizationUuid}
            componentUuid={componentUuid}
            componentType="cron"
          />
        </div>
      )}

      {templateSettingGroups.length > 0 && (
        <>
          <button
            type="button"
            onClick={() => setShowTemplateSettings(!showTemplateSettings)}
            className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors py-1"
          >
            {showTemplateSettings ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <FileCode size={14} />
            <span className="font-medium">Template Settings</span>
            {hasTemplateSettingsValues && !showTemplateSettings && (
              <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">Modified</span>
            )}
          </button>
          {showTemplateSettings && (
            <div className="space-y-3 pl-4 border-l-2 border-slate-200">
              <TemplateSettingsInput
                groups={templateSettingGroups}
                values={settings.template_settings || {}}
                onChange={(template_settings) => updateField('template_settings', template_settings)}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
