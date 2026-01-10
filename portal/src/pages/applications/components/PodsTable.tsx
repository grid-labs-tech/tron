import { FileText, Terminal, Trash2 } from 'lucide-react'
import { DataTable } from '../../../shared/components'
import { formatAge } from '../utils/formatAge'
import type { Pod } from '../../../features/components'

interface PodsTableProps {
  pods: Pod[]
  isLoading: boolean
  onViewLogs: (podName: string) => void
  onOpenConsole: (podName: string) => void
  onDeletePod: (podName: string) => void
}

export const PodsTable = ({
  pods,
  isLoading,
  onViewLogs,
  onOpenConsole,
  onDeletePod,
}: PodsTableProps) => {
  return (
    <DataTable<Pod>
      columns={[
        {
          key: 'name',
          label: 'Name',
          render: (pod) => (
            <div className="text-sm font-medium text-neutral-900">{pod.name}</div>
          ),
        },
        {
          key: 'status',
          label: 'Status',
          render: (pod) => {
            const statusClasses: Record<string, string> = {
              Running: 'badge-success',
              Pending: 'badge-warning',
              Succeeded: 'badge-info',
              Failed: 'badge-error',
              Unknown: 'badge bg-neutral-100 text-neutral-800 border-neutral-200',
            }
            const badgeClass = statusClasses[pod.status] || statusClasses.Unknown
            return (
              <span className={badgeClass}>
                {pod.status}
              </span>
            )
          },
        },
        {
          key: 'restarts',
          label: 'Restarts',
          render: (pod) => (
            <div className="text-sm text-neutral-700">{pod.restarts}</div>
          ),
        },
        {
          key: 'node',
          label: 'Node',
          render: (pod) => (
            <div className="text-sm text-neutral-700">{pod.host_ip || '-'}</div>
          ),
        },
        {
          key: 'cpu',
          label: 'CPU R/L',
          render: (pod) => (
            <div className="text-sm text-neutral-700">
              {pod.cpu_requests > 0 || pod.cpu_limits > 0
                ? `${pod.cpu_requests.toFixed(2)} / ${pod.cpu_limits.toFixed(2)}`
                : '-'}
            </div>
          ),
        },
        {
          key: 'memory',
          label: 'Mem R/L',
          render: (pod) => (
            <div className="text-sm text-neutral-700">
              {pod.memory_requests > 0 || pod.memory_limits > 0
                ? `${pod.memory_requests >= 1024 ? `${(pod.memory_requests / 1024).toFixed(1)}` : pod.memory_requests}${pod.memory_requests >= 1024 ? 'GB' : 'MB'} / ${pod.memory_limits >= 1024 ? `${(pod.memory_limits / 1024).toFixed(1)}` : pod.memory_limits}${pod.memory_limits >= 1024 ? 'GB' : 'MB'}`
                : '-'}
            </div>
          ),
        },
        {
          key: 'age',
          label: 'Age',
          render: (pod) => (
            <div className="text-sm text-neutral-700">{formatAge(pod.age_seconds)}</div>
          ),
        },
      ]}
      data={pods}
      isLoading={isLoading}
      emptyMessage="No pods found"
      loadingColor="blue"
      getRowKey={(pod) => pod.name}
      actions={(pod) => [
        {
          label: 'Logs',
          icon: <FileText size={14} />,
          onClick: () => onViewLogs(pod.name),
          variant: 'default' as const,
        },
        {
          label: 'Console',
          icon: <Terminal size={14} />,
          onClick: () => onOpenConsole(pod.name),
          variant: 'default' as const,
        },
        {
          label: 'Delete',
          icon: <Trash2 size={14} />,
          onClick: () => onDeletePod(pod.name),
          variant: 'danger' as const,
        },
      ]}
    />
  )
}
