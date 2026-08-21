import { useState } from 'react'
import { ChevronDown, ChevronRight, Settings2, FileCode } from 'lucide-react'
import type { WorkerSettings } from './types'
import type { EnvironmentSettingsLimits } from '../../features/environments'
import { CpuMemoryInput } from './form-components/CpuMemoryInput'
import { ScalingThresholdsInput } from './form-components/ScalingThresholdsInput'
import { AutoscalingInput } from './form-components/AutoscalingInput'
import { CustomMetricsInput } from './form-components/CustomMetricsInput'
import { EnvVarsInput } from './form-components/EnvVarsInput'
import { SecretsInput } from './form-components/SecretsInput'
import { CommandInput } from './form-components/CommandInput'
import { TemplateSettingsInput } from './form-components/TemplateSettingsInput'
import { useTemplateSettingsForComponent } from '../../features/templates'

interface WorkerFormProps {
  settings: WorkerSettings
  onChange: (settings: WorkerSettings) => void
  isAdmin?: boolean
  organizationUuid?: string
  componentUuid?: string
  envLimits?: EnvironmentSettingsLimits
}

export function WorkerForm({ settings, onChange, isAdmin = false, organizationUuid, componentUuid, envLimits }: WorkerFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showTemplateSettings, setShowTemplateSettings] = useState(false)
  const { data: templateSettingGroups = [] } = useTemplateSettingsForComponent(organizationUuid, 'worker')
  
  const updateField = <K extends keyof WorkerSettings>(field: K, value: WorkerSettings[K]) => {
    onChange({ ...settings, [field]: value })
  }

  // Check if any advanced settings have been modified from defaults
  const hasAdvancedChanges = () => {
    const hasEnvs = settings.envs && settings.envs.length > 0
    const hasSecrets = settings.secrets && settings.secrets.length > 0
    const commandStr = typeof settings.command === 'string'
      ? settings.command
      : ''
    const hasCommand = commandStr !== ''
    const hasCustomCpu = settings.cpu !== undefined && settings.cpu !== 0.5
    const hasCustomMemory = settings.memory !== undefined && settings.memory !== 512
    return hasEnvs || hasSecrets || hasCommand || hasCustomCpu || hasCustomMemory
  }

  const hasTemplateSettingsValues = Object.values(settings.template_settings || {}).some(
    (group) => group && Object.keys(group).length > 0
  )

  return (
    <div className="mt-3 space-y-3">
      {/* Essential Settings - Command is often essential for workers */}
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

          <AutoscalingInput
            autoscaling={settings.autoscaling}
            onChange={(autoscaling) => updateField('autoscaling', autoscaling)}
            maxReplicas={envLimits?.maxPods}
          />

          <ScalingThresholdsInput
            cpuScalingThreshold={settings.cpu_scaling_threshold}
            memoryScalingThreshold={settings.memory_scaling_threshold}
            onCpuScalingThresholdChange={(value) => updateField('cpu_scaling_threshold', value)}
            onMemoryScalingThresholdChange={(value) => updateField('memory_scaling_threshold', value)}
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
            componentType="worker"
          />

          <CustomMetricsInput
            customMetrics={settings.custom_metrics}
            onChange={(customMetrics) => updateField('custom_metrics', customMetrics)}
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
