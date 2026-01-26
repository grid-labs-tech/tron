import { X } from 'lucide-react'

interface EnvVar {
  key: string
  value: string
}

interface EnvVarsInputProps {
  envs: EnvVar[]
  onChange: (envs: EnvVar[]) => void
}

export function EnvVarsInput({ envs, onChange }: EnvVarsInputProps) {
  // Ensure envs is always an array
  const safeEnvs = Array.isArray(envs) ? envs : []

  const addEnv = () => {
    onChange([...safeEnvs, { key: '', value: '' }])
  }

  const updateEnv = (index: number, field: 'key' | 'value', value: string) => {
    const updated = safeEnvs.map((env, i) =>
      i === index ? { ...env, [field]: value } : env
    )
    onChange(updated)
  }

  const removeEnv = (index: number) => {
    onChange(safeEnvs.filter((_, i) => i !== index))
  }

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-xs font-semibold text-slate-700">Environment Variables</h5>
        <button
          type="button"
          onClick={addEnv}
          className="text-xs text-blue-600 hover:text-blue-700"
        >
          + Add
        </button>
      </div>
      {safeEnvs.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-2">No environment variables defined</p>
      ) : (
        <div className="space-y-2">
          {safeEnvs.map((env, envIndex) => (
            <div key={envIndex} className="flex items-center gap-2">
              <input
                type="text"
                value={env.key || ''}
                onChange={(e) => updateEnv(envIndex, 'key', e.target.value)}
                placeholder="KEY"
                className="flex-[2] px-2 py-1.5 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 font-mono"
              />
              <span className="text-slate-400">=</span>
              <input
                type="text"
                value={env.value || ''}
                onChange={(e) => updateEnv(envIndex, 'value', e.target.value)}
                placeholder="value"
                className="flex-[3] px-2 py-1.5 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
              />
              <button
                type="button"
                onClick={() => removeEnv(envIndex)}
                className="flex-shrink-0 p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
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
