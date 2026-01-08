interface CpuMemoryInputProps {
  cpu: number
  memory: number
  onCpuChange: (cpu: number) => void
  onMemoryChange: (memory: number) => void
}

export function CpuMemoryInput({ cpu, memory, onCpuChange, onMemoryChange }: CpuMemoryInputProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-2">
          CPU (cores) *: {cpu}
        </label>
        <input
          type="range"
          min="0.1"
          max="8"
          step="0.1"
          value={cpu}
          onChange={(e) => onCpuChange(parseFloat(e.target.value) || 0.1)}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          required
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>0.1</span>
          <span>8</span>
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-2">
          Memory (MB) *: {memory}
        </label>
        <input
          type="range"
          min="128"
          max="16384"
          step="128"
          value={memory}
          onChange={(e) => onMemoryChange(parseInt(e.target.value) || 128)}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          required
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>128 MB</span>
          <span>16 GB</span>
        </div>
      </div>
    </div>
  )
}

