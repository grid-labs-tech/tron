import { useEffect } from 'react'

interface Exposure {
  type: 'http' | 'tcp' | 'udp'
  port: number
  visibility: 'cluster' | 'private' | 'public'
}

interface ExposureInputProps {
  exposure: Exposure
  onChange: (exposure: Exposure) => void
  url?: string | null
  onUrlChange?: (url: string | null) => void
  hasGatewayApi?: boolean
  gatewayResources?: string[]
  gatewayReference?: { namespace: string; name: string }
}

export function ExposureInput({ exposure, onChange, url, onUrlChange, hasGatewayApi = true, gatewayResources = [], gatewayReference = { namespace: '', name: '' } }: ExposureInputProps) {
  const updateField = (field: keyof Exposure, value: any) => {
    onChange({ ...exposure, [field]: value })
  }

  // Limpar URL quando o tipo mudar para TCP ou UDP, ou quando visibility mudar para cluster
  useEffect(() => {
    if ((exposure.type !== 'http' || exposure.visibility === 'cluster') && url && onUrlChange) {
      onUrlChange(null)
    }
  }, [exposure.type, exposure.visibility]) // eslint-disable-line react-hooks/exhaustive-deps

  // Mapeamento de exposure.type para recursos do Gateway API
  const typeToResource: Record<'http' | 'tcp' | 'udp', string> = {
    http: 'HTTPRoute',
    tcp: 'TCPRoute',
    udp: 'UDPRoute',
  }

  // Filtrar tipos disponíveis baseado na visibilidade e recursos do Gateway API
  const getAvailableTypes = (): Array<'http' | 'tcp' | 'udp'> => {
    // Se visibility for cluster, todos os tipos estão disponíveis
    if (exposure.visibility === 'cluster') {
      return ['http', 'tcp', 'udp']
    }

    // Se visibility for public ou private, apenas tipos com recursos disponíveis no Gateway API
    if (exposure.visibility === 'public' || exposure.visibility === 'private') {
      return (['http', 'tcp', 'udp'] as const).filter((type) => {
        const requiredResource = typeToResource[type]
        return gatewayResources.includes(requiredResource)
      })
    }

    return ['http', 'tcp', 'udp']
  }

  const availableTypes = getAvailableTypes()

  // Verificar se o gateway reference está preenchido
  const hasGatewayReference = gatewayReference.namespace && gatewayReference.name

  // Se o tipo atual não estiver disponível, mudar para o primeiro disponível
  useEffect(() => {
    if (!availableTypes.includes(exposure.type) && availableTypes.length > 0) {
      onChange({ ...exposure, type: availableTypes[0] })
    }
  }, [exposure.visibility, gatewayResources.join(',')]) // eslint-disable-line react-hooks/exhaustive-deps

  // Se visibility for public/private mas não houver gateway reference, forçar para cluster
  useEffect(() => {
    if ((exposure.visibility === 'public' || exposure.visibility === 'private') && !hasGatewayReference) {
      onChange({ ...exposure, visibility: 'cluster' })
    }
  }, [hasGatewayReference]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <div className="mb-2">
        <h5 className="text-xs font-semibold text-slate-700">Exposure</h5>
      </div>
      <div className="p-2 bg-slate-50 rounded border border-slate-200">
        <div className="grid grid-cols-[0.6fr_0.6fr_2.8fr] gap-2 mb-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Type *</label>
            <select
              value={exposure.type}
              onChange={(e) => updateField('type', e.target.value)}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            >
              <option value="http" disabled={!availableTypes.includes('http')}>
                HTTP{!availableTypes.includes('http') && exposure.visibility !== 'cluster' ? ' (Not available)' : ''}
              </option>
              <option value="tcp" disabled={!availableTypes.includes('tcp')}>
                TCP{!availableTypes.includes('tcp') && exposure.visibility !== 'cluster' ? ' (Not available)' : ''}
              </option>
              <option value="udp" disabled={!availableTypes.includes('udp')}>
                UDP{!availableTypes.includes('udp') && exposure.visibility !== 'cluster' ? ' (Not available)' : ''}
              </option>
            </select>
            {exposure.visibility !== 'cluster' && availableTypes.length === 0 && (
              <p className="text-xs text-amber-600 mt-1">
                No Gateway API resources available. Please use "Cluster" visibility instead.
              </p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Port *</label>
            <input
              type="number"
              min="1"
              max="65535"
              value={exposure.port}
              onChange={(e) => updateField('port', parseInt(e.target.value) || 80)}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Visibility *</label>
            <select
              value={exposure.visibility}
              onChange={(e) => {
                const newVisibility = e.target.value as 'public' | 'private' | 'cluster'
                // Se gateway_api não estiver disponível ou não houver gateway reference, forçar cluster
                if ((!hasGatewayApi || !hasGatewayReference) && (newVisibility === 'public' || newVisibility === 'private')) {
                  updateField('visibility', 'cluster')
                } else {
                  updateField('visibility', newVisibility)
                }
              }}
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            >
              <option value="public" disabled={!hasGatewayApi || !hasGatewayReference}>
                Public - With public endpoint{(!hasGatewayApi || !hasGatewayReference) ? ' (Not available)' : ''}
              </option>
              <option value="private" disabled={!hasGatewayApi || !hasGatewayReference}>
                Private - No public endpoint{(!hasGatewayApi || !hasGatewayReference) ? ' (Not available)' : ''}
              </option>
              <option value="cluster">Cluster - Only accessible via cluster service</option>
            </select>
            {!hasGatewayApi && (
              <p className="text-xs text-amber-600 mt-1">
                Gateway API is not available. Only "Cluster" visibility is available.
              </p>
            )}
            {hasGatewayApi && !hasGatewayReference && (
              <p className="text-xs text-amber-600 mt-1">
                No Gateway created in the cluster. Only "Cluster" visibility is available.
              </p>
            )}
            <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-slate-700">
              {exposure.visibility === 'public' && (
                <p><strong className="text-blue-800">Public:</strong> The service will have a public endpoint accessible externally through Ingress.</p>
              )}
              {exposure.visibility === 'private' && (
                <p><strong className="text-blue-800">Private:</strong> The service will not have a public endpoint, only internal access.</p>
              )}
              {exposure.visibility === 'cluster' && (
                <p><strong className="text-blue-800">Cluster:</strong> The service will be accessible only via Kubernetes Service within the cluster.</p>
              )}
            </div>
          </div>
        </div>
        {onUrlChange && exposure.type === 'http' && exposure.visibility !== 'cluster' && (
          <div className="mb-3">
            <label className="block text-xs font-medium text-slate-600 mb-1">URL *</label>
            <input
              type="text"
              value={url || ''}
              onChange={(e) => onUrlChange(e.target.value || null)}
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
              placeholder="myapp.example.com"
              required
            />
            <p className="text-xs text-slate-500 mt-1">This URL will be used as the vhost for the Ingress</p>
          </div>
        )}
      </div>
    </div>
  )
}

