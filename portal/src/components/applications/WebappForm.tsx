import type { WebappSettings } from './types'
import { CpuMemoryInput } from './form-components/CpuMemoryInput'
import { ScalingThresholdsInput } from './form-components/ScalingThresholdsInput'
import { AutoscalingInput } from './form-components/AutoscalingInput'
import { HealthcheckInput } from './form-components/HealthcheckInput'
import { ExposureInput } from './form-components/ExposureInput'
import { CustomMetricsInput } from './form-components/CustomMetricsInput'
import { EnvVarsInput } from './form-components/EnvVarsInput'
import { CommandInput } from './form-components/CommandInput'

interface WebappFormProps {
  settings: WebappSettings
  onChange: (settings: WebappSettings) => void
  url?: string | null
  onUrlChange?: (url: string | null) => void
  hasGatewayApi?: boolean
  gatewayResources?: string[]
  gatewayReference?: { namespace: string; name: string }
}

export function WebappForm({ settings, onChange, url, onUrlChange, hasGatewayApi = true, gatewayResources = [], gatewayReference = { namespace: '', name: '' } }: WebappFormProps) {
  const updateField = <K extends keyof WebappSettings>(field: K, value: WebappSettings[K]) => {
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

      <ExposureInput
        exposure={settings.exposure}
        onChange={(exposure) => updateField('exposure', exposure)}
        url={url}
        onUrlChange={onUrlChange}
        hasGatewayApi={hasGatewayApi}
        gatewayResources={gatewayResources}
        gatewayReference={gatewayReference}
      />

      <HealthcheckInput
        healthcheck={settings.healthcheck}
        onChange={(healthcheck) => updateField('healthcheck', healthcheck)}
      />

      <CustomMetricsInput
        customMetrics={settings.custom_metrics}
        onChange={(customMetrics) => updateField('custom_metrics', customMetrics)}
      />

      <EnvVarsInput
        envs={settings.envs}
        onChange={(envs) => updateField('envs', envs)}
      />

      <CommandInput
        command={settings.command}
        onChange={(command) => updateField('command', command)}
      />
    </div>
  )
}

