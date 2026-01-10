import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Clock } from 'lucide-react'
import { useInstance, useInstanceEvents } from '../../features/instances'
import { useApplication } from '../../features/applications'
import type { KubernetesEvent } from '../../features/instances'
import { Breadcrumbs, PageHeader, DataTable } from '../../shared/components'

function InstanceEvents() {
  const { uuid: applicationUuid, instanceUuid } = useParams<{
    uuid: string
    instanceUuid: string
  }>()

  const { data: instance } = useInstance(instanceUuid)
  const { data: application } = useApplication(applicationUuid)
  const [refreshInterval, setRefreshInterval] = useState<number>(10000) // Default: 10 seconds

  const { data: events = [], isLoading: isLoadingEvents } = useInstanceEvents(instanceUuid)

  const formatAge = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      return `${minutes}m`
    } else if (seconds < 86400) {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}h${minutes}m`
    } else {
      const days = Math.floor(seconds / 86400)
      const hours = Math.floor((seconds % 86400) / 3600)
      return `${days}d${hours}h`
    }
  }

  const formatDateTime = (isoString: string | null): string => {
    if (!isoString) return '-'
    try {
      const date = new Date(isoString)
      return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return isoString
    }
  }

  if (!instance || !application) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Applications', path: '/applications' },
          { label: application?.name || 'Application' },
          { label: instance?.environment.name || 'Environment', path: `/applications/${applicationUuid}/instances/${instanceUuid}/components` },
          { label: 'Components', path: `/applications/${applicationUuid}/instances/${instanceUuid}/components` },
          { label: 'Events' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader
          title="Kubernetes Events"
          description={`Events for ${application?.name || 'Application'} • ${instance?.environment.name || 'Environment'} • ${instance.image}:${instance.version}`}
        />
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-neutral-700">
            <span>Refresh:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="input pr-10"
            >
              <option value={0}>Disabled</option>
              <option value={5000}>5 seconds</option>
              <option value={10000}>10 seconds</option>
              <option value={30000}>30 seconds</option>
              <option value={60000}>1 minute</option>
            </select>
          </label>
        </div>
      </div>

      <div className="overflow-x-auto w-full">
        <div className="min-w-full">
          <DataTable<KubernetesEvent>
            columns={[
              {
                key: 'type',
                label: 'Type',
                width: '100px',
                render: (event) => {
                  const typeClasses: Record<string, string> = {
                    Normal: 'badge-success',
                    Warning: 'badge-warning',
                  }
                  const badgeClass = typeClasses[event.type] || 'badge bg-neutral-100 text-neutral-800 border-neutral-200'
                  return (
                    <span className={badgeClass}>
                      {event.type}
                    </span>
                  )
                },
              },
              {
                key: 'reason',
                label: 'Reason',
                width: '150px',
                render: (event) => (
                  <div className="text-sm font-medium text-neutral-900">{event.reason}</div>
                ),
              },
              {
                key: 'involved_object',
                label: 'Object',
                width: '200px',
                render: (event) => (
                  <div>
                    <div className="text-sm font-medium text-neutral-800">
                      {event.involved_object.kind || 'Unknown'}/{event.involved_object.name || '-'}
                    </div>
                    {event.involved_object.namespace && (
                      <small className="text-xs text-neutral-500">{event.involved_object.namespace}</small>
                    )}
                  </div>
                ),
              },
              {
                key: 'message',
                label: 'Message',
                width: '300px',
                render: (event) => (
                  <div className="text-sm text-neutral-700 max-w-xs truncate" title={event.message}>
                    {event.message || '-'}
                  </div>
                ),
              },
              {
                key: 'source',
                label: 'Source',
                width: '150px',
                render: (event) => (
                  <div className="text-sm text-neutral-600">
                    {event.source.component && (
                      <div className="truncate">{event.source.component}</div>
                    )}
                    {event.source.host && (
                      <small className="text-xs text-neutral-500 truncate block">{event.source.host}</small>
                    )}
                    {!event.source.component && !event.source.host && '-'}
                  </div>
                ),
              },
              {
                key: 'count',
                label: 'Count',
                width: '80px',
                render: (event) => (
                  <div className="text-sm font-medium text-neutral-800">{event.count}</div>
                ),
              },
              {
                key: 'first_timestamp',
                label: 'First Seen',
                width: '180px',
                render: (event) => (
                  <div className="text-sm text-neutral-700 whitespace-nowrap">{formatDateTime(event.first_timestamp)}</div>
                ),
              },
              {
                key: 'last_timestamp',
                label: 'Last Seen',
                width: '180px',
                render: (event) => (
                  <div className="text-sm text-neutral-700 whitespace-nowrap">{formatDateTime(event.last_timestamp)}</div>
                ),
              },
              {
                key: 'age',
                label: 'Age',
                width: '100px',
                render: (event) => (
                  <div className="text-sm text-neutral-700 flex items-center gap-1 whitespace-nowrap">
                    <Clock size={14} className="text-neutral-400" />
                    {formatAge(event.age_seconds)}
                  </div>
                ),
              },
            ]}
            data={events}
            isLoading={isLoadingEvents}
            emptyMessage="No events found"
            loadingColor="blue"
            getRowKey={(event) => event.name}
          />
        </div>
      </div>
    </div>
  )
}

export default InstanceEvents

