interface Endpoint {
  source_protocol: 'http' | 'https' | 'tcp' | 'tls'
  source_port: number
  dest_protocol: 'http' | 'https' | 'tcp' | 'tls'
  dest_port: number
}

interface EndpointsInputProps {
  endpoints: Endpoint
  onChange: (endpoints: Endpoint) => void
}

export function EndpointsInput({ endpoints, onChange }: EndpointsInputProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const updateField = (field: keyof Endpoint, value: any) => {
    onChange({ ...endpoints, [field]: value })
  }

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <div className="mb-2">
        <h5 className="text-xs font-semibold text-slate-700">Endpoint</h5>
      </div>
      <div className="p-2 bg-slate-50 rounded border border-slate-200">
        <div className="grid grid-cols-4 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Source Protocol</label>
            <select
              value={endpoints.source_protocol}
              onChange={(e) => updateField('source_protocol', e.target.value)}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            >
              <option value="http">HTTP</option>
              <option value="https">HTTPS</option>
              <option value="tcp">TCP</option>
              <option value="tls">TLS</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Source Port</label>
            <input
              type="number"
              min="1"
              max="65535"
              value={endpoints.source_port}
              onChange={(e) => updateField('source_port', parseInt(e.target.value) || 80)}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Dest Protocol</label>
            <select
              value={endpoints.dest_protocol}
              onChange={(e) => updateField('dest_protocol', e.target.value)}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            >
              <option value="http">HTTP</option>
              <option value="https">HTTPS</option>
              <option value="tcp">TCP</option>
              <option value="tls">TLS</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Dest Port</label>
            <input
              type="number"
              min="1"
              max="65535"
              value={endpoints.dest_port}
              onChange={(e) => updateField('dest_port', parseInt(e.target.value) || 8080)}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

