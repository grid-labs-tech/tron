import type { WorkerSettings } from './types'
import { CpuMemoryInput } from './form-components/CpuMemoryInput'
import { ScalingThresholdsInput } from './form-components/ScalingThresholdsInput'
import { AutoscalingInput } from './form-components/AutoscalingInput'
import { CustomMetricsInput } from './form-components/CustomMetricsInput'
import { EnvVarsInput } from './form-components/EnvVarsInput'
import { CommandInput } from './form-components/CommandInput'

interface WorkerFormProps {
  settings: WorkerSettings
  onChange: (settings: WorkerSettings) => void
}

export function WorkerForm({ settings, onChange }: WorkerFormProps) {
  const updateField = <K extends keyof WorkerSettings>(field: K, value: WorkerSettings[K]) => {
    onChange({ ...settings, [field]: value })
  }

  return (
    <div className="mt-4 pt-4 border-t border-slate-200 space-y-4">
      <h4 className="text-sm font-semibold text-slate-700">Settings</h4>

      <CpuMemoryInput
        cpu={settings.cpu}
        memory={settings.memory}
        onCpuChange={(cpu) => updateField('cpu', cpu)}
        onMemoryChange={(memory) => updateField('memory', memory)}
      />

      <ScalingThresholdsInput
        cpuScalingThreshold={settings.cpu_scaling_threshold}
        memoryScalingThreshold={settings.memory_scaling_threshold}
        onCpuScalingThresholdChange={(value) => updateField('cpu_scaling_threshold', value)}
        onMemoryScalingThresholdChange={(value) => updateField('memory_scaling_threshold', value)}
      />

      <AutoscalingInput
        autoscaling={settings.autoscaling}
        onChange={(autoscaling) => updateField('autoscaling', autoscaling)}
      />

      <CustomMetricsInput
        customMetrics={settings.custom_metrics}
        onChange={(customMetrics) => updateField('custom_metrics', customMetrics)}
      />

      <CommandInput
        command={settings.command}
        onChange={(command) => updateField('command', command)}
      />

      <EnvVarsInput
        envs={settings.envs}
        onChange={(envs) => updateField('envs', envs)}
      />
    </div>
  )
}

