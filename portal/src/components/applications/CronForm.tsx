import { useState } from 'react'
import { ChevronDown, ChevronRight, Settings2 } from 'lucide-react'
import type { CronSettings } from './types'
import { CpuMemoryInput } from './form-components/CpuMemoryInput'
import { ScheduleInput } from './form-components/ScheduleInput'
import { EnvVarsInput } from './form-components/EnvVarsInput'
import { SecretsInput } from './form-components/SecretsInput'
import { CommandInput } from './form-components/CommandInput'

interface CronFormProps {
  settings: CronSettings
  onChange: (settings: CronSettings) => void
  isAdmin?: boolean
  componentUuid?: string
}

export function CronForm({ settings, onChange, isAdmin = false, componentUuid }: CronFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  
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
          />

          <EnvVarsInput
            envs={settings.envs}
            onChange={(envs) => updateField('envs', envs)}
          />

          <SecretsInput
            secrets={settings.secrets || []}
            onChange={(secrets) => updateField('secrets', secrets)}
            isAdmin={isAdmin}
            componentUuid={componentUuid}
            componentType="cron"
          />
        </div>
      )}
    </div>
  )
}
