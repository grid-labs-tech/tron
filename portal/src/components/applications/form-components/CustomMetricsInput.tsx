interface CustomMetrics {
  enabled: boolean
  path: string
  port: number
}

interface CustomMetricsInputProps {
  customMetrics: CustomMetrics
  onChange: (customMetrics: CustomMetrics) => void
}

export function CustomMetricsInput({ customMetrics, onChange }: CustomMetricsInputProps) {
  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-xs font-semibold text-slate-700">Custom Metrics</h5>
        <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
          <input
            type="checkbox"
            checked={customMetrics.enabled}
            onChange={(e) => {
              onChange({
                ...customMetrics,
                enabled: e.target.checked,
              })
            }}
            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          Enabled
        </label>
      </div>
      {customMetrics.enabled && (
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Path</label>
            <input
              type="text"
              value={customMetrics.path}
              onChange={(e) => {
                onChange({
                  ...customMetrics,
                  path: e.target.value,
                })
              }}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Port</label>
            <input
              type="number"
              min="1"
              max="65535"
              value={customMetrics.port}
              onChange={(e) => {
                onChange({
                  ...customMetrics,
                  port: parseInt(e.target.value) || 8080,
                })
              }}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
        </div>
      )}
    </div>
  )
}

