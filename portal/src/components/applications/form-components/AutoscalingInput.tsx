interface Autoscaling {
  min: number
  max: number
}

interface AutoscalingInputProps {
  autoscaling: Autoscaling | undefined
  onChange: (autoscaling: Autoscaling) => void
}

export function AutoscalingInput({ autoscaling, onChange }: AutoscalingInputProps) {
  // Valores padrão caso autoscaling não esteja definido
  const safeAutoscaling: Autoscaling = autoscaling || { min: 2, max: 10 }

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <h5 className="text-xs font-semibold text-slate-700 mb-3">Autoscaling</h5>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-2">
            Min Replicas: {safeAutoscaling.min}
          </label>
          <input
            type="range"
            min="1"
            max="20"
            step="1"
            value={safeAutoscaling.min}
            onChange={(e) => {
              const min = parseInt(e.target.value) || 1
              // Garantir que min não seja maior que max
              const newMax = Math.max(min, safeAutoscaling.max)
              onChange({ min, max: newMax })
            }}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>1</span>
            <span>20</span>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-2">
            Max Replicas: {safeAutoscaling.max}
          </label>
          <input
            type="range"
            min="1"
            max="20"
            step="1"
            value={safeAutoscaling.max}
            onChange={(e) => {
              const max = parseInt(e.target.value) || 10
              // Garantir que max não seja menor que min
              const newMin = Math.min(max, safeAutoscaling.min)
              onChange({ min: newMin, max })
            }}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>1</span>
            <span>20</span>
          </div>
        </div>
      </div>
    </div>
  )
}

