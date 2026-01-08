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
  const addEnv = () => {
    onChange([...envs, { key: '', value: '' }])
  }

  const updateEnv = (index: number, field: 'key' | 'value', value: string) => {
    const updated = envs.map((env, i) =>
      i === index ? { ...env, [field]: value } : env
    )
    onChange(updated)
  }

  const removeEnv = (index: number) => {
    onChange(envs.filter((_, i) => i !== index))
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
      {envs.map((env, envIndex) => (
        <div key={envIndex} className="mb-2 grid grid-cols-3 gap-2">
          <div>
            <input
              type="text"
              value={env.key}
              onChange={(e) => updateEnv(envIndex, 'key', e.target.value)}
              placeholder="Key"
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
          <div>
            <input
              type="text"
              value={env.value}
              onChange={(e) => updateEnv(envIndex, 'value', e.target.value)}
              placeholder="Value"
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
          <button
            type="button"
            onClick={() => removeEnv(envIndex)}
            className="px-2 py-1 text-red-600 hover:bg-red-50 rounded text-xs"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}

