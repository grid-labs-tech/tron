interface Healthcheck {
  path: string
  protocol: 'http' | 'tcp'
  port: number
  timeout: number
  interval: number
  initial_interval: number
  failure_threshold: number
}

interface HealthcheckInputProps {
  healthcheck: Healthcheck
  onChange: (healthcheck: Healthcheck) => void
}

export function HealthcheckInput({ healthcheck, onChange }: HealthcheckInputProps) {
  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <h5 className="text-xs font-semibold text-slate-700 mb-2">Healthcheck</h5>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Protocol</label>
          <select
            value={healthcheck.protocol}
            onChange={(e) => {
              onChange({
                ...healthcheck,
                protocol: e.target.value as 'http' | 'tcp',
              })
            }}
            className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
          >
            <option value="http">HTTP</option>
            <option value="tcp">TCP</option>
          </select>
        </div>
        {healthcheck.protocol === 'http' && (
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Path</label>
            <input
              type="text"
              value={healthcheck.path}
              onChange={(e) => {
                onChange({
                  ...healthcheck,
                  path: e.target.value,
                })
              }}
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
        )}
        {healthcheck.protocol === 'tcp' && (
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Port *</label>
            <input
              type="number"
              min="1"
              max="65535"
              value={healthcheck.port}
              onChange={(e) => {
                onChange({
                  ...healthcheck,
                  port: parseInt(e.target.value) || 80,
                })
              }}
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
              required
            />
          </div>
        )}
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Timeout (s)</label>
          <input
            type="number"
            min="1"
            value={healthcheck.timeout}
            onChange={(e) => {
              onChange({
                ...healthcheck,
                timeout: parseInt(e.target.value) || 3,
              })
            }}
            className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Interval (s)</label>
          <input
            type="number"
            min="1"
            value={healthcheck.interval}
            onChange={(e) => {
              onChange({
                ...healthcheck,
                interval: parseInt(e.target.value) || 15,
              })
            }}
            className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Initial Interval (s)</label>
          <input
            type="number"
            min="1"
            value={healthcheck.initial_interval}
            onChange={(e) => {
              onChange({
                ...healthcheck,
                initial_interval: parseInt(e.target.value) || 15,
              })
            }}
            className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Failure Threshold</label>
          <input
            type="number"
            min="1"
            value={healthcheck.failure_threshold}
            onChange={(e) => {
              onChange({
                ...healthcheck,
                failure_threshold: parseInt(e.target.value) || 2,
              })
            }}
            className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
          />
        </div>
      </div>
    </div>
  )
}

