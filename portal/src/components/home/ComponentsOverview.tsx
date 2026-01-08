import type { ComponentStats } from '../../types'
import { Globe, PlayCircle, Clock, CheckCircle2 } from 'lucide-react'

interface ComponentsOverviewProps {
  components: ComponentStats
}

export function ComponentsOverview({ components }: ComponentsOverviewProps) {
  if (components.total === 0) {
    return null
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">Components Overview</h2>
        <p className="text-slate-600 text-sm">
          Detailed breakdown of all components deployed across your platform. Components are the building blocks
          of your applications, including web applications, background workers, and scheduled cron jobs.
        </p>
      </div>
      <div className="bg-white rounded-xl p-6 shadow-soft border border-slate-200/60">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="group relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-purple-50 to-purple-100/50 border border-purple-200 hover:border-purple-300 hover:shadow-md transition-all duration-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Globe className="text-purple-600" size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Webapp</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{components.webapp}</p>
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Web applications exposed to users via HTTP/HTTPS endpoints with ingress configuration.
            </p>
          </div>

          <div className="group relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-orange-50 to-orange-100/50 border border-orange-200 hover:border-orange-300 hover:shadow-md transition-all duration-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <PlayCircle className="text-orange-600" size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Worker</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{components.worker}</p>
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Background workers that process jobs and tasks asynchronously with auto-scaling capabilities.
            </p>
          </div>

          <div className="group relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-blue-50 to-blue-100/50 border border-blue-200 hover:border-blue-300 hover:shadow-md transition-all duration-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Clock className="text-blue-600" size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Cron</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{components.cron}</p>
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Scheduled jobs that run at specified intervals using cron expressions for automation.
            </p>
          </div>

          <div className="group relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-green-50 to-green-100/50 border border-green-200 hover:border-green-300 hover:shadow-md transition-all duration-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="text-green-600" size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Enabled</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{components.enabled}</p>
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Currently active components that are deployed and running in your Kubernetes clusters.
            </p>
          </div>
        </div>
        <div className="mt-6 pt-6 border-t border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-700">Total Components</p>
              <p className="text-xs text-slate-500 mt-0.5">Across all types and environments</p>
            </div>
            <p className="text-3xl font-bold text-slate-900">{components.total}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

