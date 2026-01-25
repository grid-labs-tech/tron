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
  const updateField = <K extends keyof CronSettings>(field: K, value: CronSettings[K]) => {
    onChange({ ...settings, [field]: value })
  }

  return (
    <div className="mt-4 pt-4 border-t border-slate-200 space-y-4">
      <h4 className="text-sm font-semibold text-slate-700">Settings</h4>

      {/* Schedule - obrigatório para cron */}
      <ScheduleInput
        schedule={settings.schedule}
        onChange={(schedule) => updateField('schedule', schedule)}
      />

      {/* CPU e Memory */}
      <CpuMemoryInput
        cpu={settings.cpu}
        memory={settings.memory}
        onCpuChange={(cpu) => updateField('cpu', cpu)}
        onMemoryChange={(memory) => updateField('memory', memory)}
      />

      {/* Command */}
      <CommandInput
        command={settings.command}
        onChange={(command) => updateField('command', command)}
      />

      {/* Environment Variables */}
      <EnvVarsInput
        envs={settings.envs}
        onChange={(envs) => updateField('envs', envs)}
      />

      {/* Secrets */}
      <SecretsInput
        secrets={settings.secrets || []}
        onChange={(secrets) => updateField('secrets', secrets)}
        isAdmin={isAdmin}
        componentUuid={componentUuid}
        componentType="cron"
      />
    </div>
  )
}

