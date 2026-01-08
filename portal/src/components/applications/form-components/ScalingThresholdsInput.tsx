interface ScalingThresholdsInputProps {
  cpuScalingThreshold: number
  memoryScalingThreshold: number
  onCpuScalingThresholdChange: (value: number) => void
  onMemoryScalingThresholdChange: (value: number) => void
}

export function ScalingThresholdsInput({
  cpuScalingThreshold,
  memoryScalingThreshold,
  onCpuScalingThresholdChange,
  onMemoryScalingThresholdChange,
}: ScalingThresholdsInputProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-2">
          CPU Scaling Threshold (%): {cpuScalingThreshold}
        </label>
        <input
          type="range"
          min="1"
          max="100"
          step="1"
          value={cpuScalingThreshold}
          onChange={(e) => onCpuScalingThresholdChange(parseInt(e.target.value) || 80)}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>1%</span>
          <span>100%</span>
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-2">
          Memory Scaling Threshold (%): {memoryScalingThreshold}
        </label>
        <input
          type="range"
          min="1"
          max="100"
          step="1"
          value={memoryScalingThreshold}
          onChange={(e) => onMemoryScalingThresholdChange(parseInt(e.target.value) || 80)}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>1%</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  )
}

