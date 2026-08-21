export interface EnvironmentSettingItem {
  key: string
  value: string | number | boolean | string[] | Record<string, unknown>
  description: string
  type: string
}

export interface EnvironmentClusterSummary {
  uuid: string
  name: string
}

export interface Environment {
  uuid: string
  name: string
  created_at: string
  updated_at: string
  clusters?: EnvironmentClusterSummary[]
  settings?: EnvironmentSettingItem[]
}

export interface EnvironmentCreate {
  name: string
}

export type EnvironmentSettingsUpdate = Record<
  string,
  string | number | boolean | string[] | Record<string, unknown>
>

/** Limits derived from environment settings for component forms (CPU, memory, max replicas). */
export interface EnvironmentSettingsLimits {
  minCpuCores: number
  maxCpuCores: number
  minMemoryMegabytes: number
  maxMemoryMegabytes: number
  maxPods?: number
}

const DEFAULT_ENV_LIMITS: EnvironmentSettingsLimits = {
  minCpuCores: 0.25,
  maxCpuCores: 8,
  minMemoryMegabytes: 128,
  maxMemoryMegabytes: 8192,
  maxPods: 20,
}

/** Build limits from environment.settings array (key/value). Uses defaults when missing. */
export function getEnvironmentSettingsLimits(
  settings: EnvironmentSettingItem[] | undefined
): EnvironmentSettingsLimits {
  if (!settings?.length) return { ...DEFAULT_ENV_LIMITS }
  const byKey: Record<string, number> = {}
  for (const item of settings) {
    if (typeof item.value === 'number') byKey[item.key] = item.value
  }
  return {
    minCpuCores: byKey.min_cpu_cores ?? DEFAULT_ENV_LIMITS.minCpuCores,
    maxCpuCores: byKey.max_cpu_cores ?? DEFAULT_ENV_LIMITS.maxCpuCores,
    minMemoryMegabytes: byKey.min_memory_megabytes ?? DEFAULT_ENV_LIMITS.minMemoryMegabytes,
    maxMemoryMegabytes: byKey.max_memory_megabytes ?? DEFAULT_ENV_LIMITS.maxMemoryMegabytes,
    maxPods: byKey.max_pods ?? DEFAULT_ENV_LIMITS.maxPods,
  }
}
