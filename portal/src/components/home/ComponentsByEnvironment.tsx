import { Globe } from 'lucide-react'

interface ComponentsByEnvironmentProps {
  componentsByEnvironment: Record<string, number>
}

export function ComponentsByEnvironment({ componentsByEnvironment }: ComponentsByEnvironmentProps) {
  if (Object.keys(componentsByEnvironment).length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-soft border border-slate-200/60">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-indigo-100 rounded-lg">
          <Globe className="text-indigo-600" size={20} />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Components by Environment</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Distribution of components across different environments
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(componentsByEnvironment).map(([envName, count]) => (
          <div
            key={envName}
            className="group flex items-center justify-between p-4 bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-lg border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-indigo-500 group-hover:bg-indigo-600 transition-colors" />
              <span className="text-sm font-medium text-slate-700">{envName}</span>
            </div>
            <span className="text-xl font-bold text-slate-900">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
