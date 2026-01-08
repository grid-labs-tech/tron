import { useQuery } from '@tanstack/react-query'
import { environmentsApi } from '../../services/api'
import { InfoCard } from './InfoCard'
import type { InstanceCreate } from '../../types'

interface InstanceFormProps {
  data: Omit<InstanceCreate, 'application_uuid'>
  onChange: (data: Omit<InstanceCreate, 'application_uuid'>) => void
  showInfoCard?: boolean
}

export function InstanceForm({ data, onChange, showInfoCard = true }: InstanceFormProps) {
  const { data: environments = [] } = useQuery({
    queryKey: ['environments'],
    queryFn: environmentsApi.list,
  })

  return (
    <div className="bg-white rounded-xl shadow-soft border border-slate-200/60 p-6">
      <h2 className="text-xl font-semibold text-slate-800 mb-4">Instance</h2>

      {showInfoCard && (
        <InfoCard>
          <p className="text-sm text-blue-900 leading-relaxed">
            An instance represents a specific deployment of your application in a particular environment.
            It defines the container image and version that will be used to run your application components.
            Each instance belongs to one application and one environment, and can contain multiple components
            (such as webapps, workers, or cron jobs) that share the same container image and version.
          </p>
        </InfoCard>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Environment *</label>
          <select
            value={data.environment_uuid}
            onChange={(e) => onChange({ ...data, environment_uuid: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
            required
          >
            <option value="">Select an environment</option>
            {environments.map((env) => (
              <option key={env.uuid} value={env.uuid}>
                {env.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Image *</label>
          <input
            type="text"
            value={data.image}
            onChange={(e) => onChange({ ...data, image: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
            placeholder="my-image"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Version *</label>
          <input
            type="text"
            value={data.version}
            onChange={(e) => onChange({ ...data, version: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
            placeholder="v1.0.0"
            required
          />
        </div>
      </div>
    </div>
  )
}

