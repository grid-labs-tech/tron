import { Link } from 'react-router-dom'
import { LucideIcon } from 'lucide-react'

interface Stat {
  label: string
  value: number
  icon: LucideIcon
  path: string
  bgColor: string
  iconColor: string
  borderColor: string
  description: string
}

interface StatsGridProps {
  stats: Stat[]
}

export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">Platform Statistics</h2>
        <p className="text-slate-600 text-sm">
          Overview of your infrastructure resources. Click on any card to view details and manage resources.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Link
              key={stat.label}
              to={stat.path}
              className="group relative overflow-hidden rounded-xl bg-white border border-slate-200/60 shadow-soft hover:shadow-soft-lg transition-all duration-300 hover:-translate-y-1"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 ${stat.bgColor} rounded-xl shadow-sm`}>
                    <Icon className={stat.iconColor} size={24} />
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-slate-900 mb-1">{stat.value}</p>
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                      {stat.label}
                    </p>
                  </div>
                </div>
                <p className="text-sm text-slate-600 leading-relaxed">
                  {stat.description}
                </p>
              </div>
              <div className={`absolute bottom-0 left-0 right-0 h-1 ${stat.bgColor} transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300`} />
            </Link>
          )
        })}
      </div>
    </div>
  )
}
