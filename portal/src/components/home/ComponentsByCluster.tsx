import { Cloud } from 'lucide-react'

interface ComponentsByClusterProps {
  componentsByCluster: Record<string, number>
}

export function ComponentsByCluster({ componentsByCluster }: ComponentsByClusterProps) {
  if (Object.keys(componentsByCluster).length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-soft border border-slate-200/60">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-blue-100 rounded-lg">
          <Cloud className="text-blue-600" size={20} />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Components by Cluster</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Distribution of components across Kubernetes clusters
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(componentsByCluster).map(([clusterName, count]) => (
          <div
            key={clusterName}
            className="group flex items-center justify-between p-4 bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-lg border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-blue-500 group-hover:bg-blue-600 transition-colors" />
              <span className="text-sm font-medium text-slate-700">{clusterName}</span>
            </div>
            <span className="text-xl font-bold text-slate-900">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
