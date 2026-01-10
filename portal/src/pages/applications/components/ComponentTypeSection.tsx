import { ChevronDown, ChevronRight, Server, Pencil, Trash2 } from 'lucide-react'
import { DataTable } from '../../../shared/components'
import type { InstanceComponent } from '../../../features/instances'

interface ComponentTypeSectionProps {
  type: 'webapp' | 'worker' | 'cron'
  components: InstanceComponent[]
  isExpanded: boolean
  onToggle: () => void
  columns: Array<{
    key: string
    label: string
    render: (component: InstanceComponent) => React.ReactNode
  }>
  applicationUuid: string
  instanceUuid: string
  onEdit: (component: InstanceComponent) => void
  onDelete: (componentUuid: string) => void
}

export const ComponentTypeSection = ({
  type,
  components,
  isExpanded,
  onToggle,
  columns,
  applicationUuid,
  instanceUuid,
  onEdit,
  onDelete,
}: ComponentTypeSectionProps) => {
  const count = components.length

  if (count === 0) return null

  return (
    <div className="bg-white rounded-xl shadow-soft border border-slate-200/60 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown size={20} className="text-slate-600" />
          ) : (
            <ChevronRight size={20} className="text-slate-600" />
          )}
          <span className="text-lg font-semibold text-slate-800 capitalize">{type}</span>
          <span className="text-sm text-slate-500">({count} component{count !== 1 ? 's' : ''})</span>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-slate-200">
          <DataTable<InstanceComponent>
            columns={columns}
            data={components}
            isLoading={false}
            emptyMessage="No components found"
            loadingColor="blue"
            getRowKey={(component) => component.uuid}
            actions={(component) => {
              const actions = []

              // Add "PODs" only for webapp
              if (type === 'webapp') {
                actions.push({
                  label: 'PODs',
                  icon: <Server size={14} />,
                  onClick: () => {
                    window.location.href = `/applications/${applicationUuid}/instances/${instanceUuid}/components/${component.uuid}`
                  },
                  variant: 'default' as const,
                })
              }

              // Add "Executions" only for cron
              if (type === 'cron') {
                actions.push({
                  label: 'Executions',
                  icon: <Server size={14} />,
                  onClick: () => {
                    window.location.href = `/applications/${applicationUuid}/instances/${instanceUuid}/components/${component.uuid}/executions`
                  },
                  variant: 'default' as const,
                })
              }

              actions.push(
                {
                  label: 'Edit',
                  icon: <Pencil size={14} />,
                  onClick: () => onEdit(component),
                  variant: 'default' as const,
                },
                {
                  label: 'Delete',
                  icon: <Trash2 size={14} />,
                  onClick: () => onDelete(component.uuid),
                  variant: 'danger' as const,
                }
              )

              return actions
            }}
          />
        </div>
      )}
    </div>
  )
}
