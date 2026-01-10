import type { InstanceComponent } from '../../../features/instances'

export const getBaseColumns = () => [
  {
    key: 'name',
    label: 'Name',
    render: (component: InstanceComponent) => (
      <div>
        <div className="text-sm font-medium text-slate-800">{component.name}</div>
      </div>
    ),
  },
  {
    key: 'url',
    label: 'URL',
    render: (component: InstanceComponent) => (
      <div className="text-sm text-slate-600">{component.url || '-'}</div>
    ),
  },
  {
    key: 'cpu',
    label: 'CPU',
    render: (component: InstanceComponent) => (
      <div className="text-sm text-slate-600">
        {component.settings?.cpu ? `${component.settings.cpu} cores` : 'N/A'}
      </div>
    ),
  },
  {
    key: 'memory',
    label: 'Memory',
    render: (component: InstanceComponent) => (
      <div className="text-sm text-slate-600">
        {component.settings?.memory
          ? `${component.settings.memory >= 1024 ? `${(component.settings.memory / 1024).toFixed(1)} GB` : `${component.settings.memory} MB`}`
          : 'N/A'}
      </div>
    ),
  },
  {
    key: 'status',
    label: 'Status',
    render: (component: InstanceComponent) => (
      <div>
        {component.enabled ? (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Enabled
          </span>
        ) : (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Disabled
          </span>
        )}
      </div>
    ),
  },
]

export const getWebappColumns = () => [
  {
    key: 'exposure',
    label: 'Exposure',
    render: (component: InstanceComponent) => {
      const settings = (component.settings as any) || {}
      let exposure = settings.exposure

      if (!exposure && settings.endpoints) {
        const oldEndpoints = settings.endpoints
        let oldEndpoint: any = null
        if (Array.isArray(oldEndpoints)) {
          oldEndpoint = oldEndpoints.length > 0 ? oldEndpoints[0] : null
        } else if (oldEndpoints && typeof oldEndpoints === 'object') {
          oldEndpoint = oldEndpoints
        }
        if (oldEndpoint) {
          exposure = {
            type: oldEndpoint.source_protocol || 'http',
            port: oldEndpoint.source_port || 80,
            visibility: 'cluster',
          }
        }
      }

      if (!exposure || !exposure.port) {
        return <div className="text-sm text-slate-400">No exposure</div>
      }

      return (
        <div className="text-sm text-slate-600">
          <div className="text-xs">
            {exposure.type}:{exposure.port} ({exposure.visibility})
          </div>
        </div>
      )
    },
  },
  {
    key: 'visibility',
    label: 'Visibility',
    render: (component: InstanceComponent) => {
      let visibility = 'cluster'
      const settings = component.settings || {}
      if (settings.exposure && settings.exposure.visibility) {
        visibility = settings.exposure.visibility
      }

      return (
        <div>
          {visibility === 'public' ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Public
            </span>
          ) : visibility === 'cluster' ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              Cluster
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
              Private
            </span>
          )}
        </div>
      )
    },
  },
  {
    key: 'autoscaling',
    label: 'Autoscaling',
    render: (component: InstanceComponent) => {
      const autoscaling = (component.settings as any)?.autoscaling
      if (!autoscaling || (autoscaling.min === undefined && autoscaling.max === undefined)) {
        return <div className="text-sm text-slate-400">N/A</div>
      }
      return (
        <div className="text-sm text-slate-600">
          {autoscaling.min ?? '-'} - {autoscaling.max ?? '-'}
        </div>
      )
    },
  },
]

export const getCronColumns = () => [
  {
    key: 'command',
    label: 'Command',
    render: (component: InstanceComponent) => {
      const command = (component.settings as any)?.command
      if (!command) {
        return <div className="text-sm text-slate-400">No command</div>
      }
      const commandStr = Array.isArray(command) ? command.join(' ') : command
      return (
        <div className="text-sm text-slate-600 font-mono text-xs">
          {commandStr}
        </div>
      )
    },
  },
  {
    key: 'schedule',
    label: 'Schedule',
    render: (component: InstanceComponent) => {
      const schedule = (component.settings as any)?.schedule
      if (!schedule) {
        return <div className="text-sm text-slate-400">No schedule</div>
      }
      return (
        <div className="text-sm text-slate-600 font-mono text-xs">
          {schedule}
        </div>
      )
    },
  },
]

export const getWorkerColumns = () => [
  {
    key: 'autoscaling',
    label: 'Autoscaling',
    render: (component: InstanceComponent) => {
      const autoscaling = (component.settings as any)?.autoscaling
      if (!autoscaling || (autoscaling.min === undefined && autoscaling.max === undefined)) {
        return <div className="text-sm text-slate-400">N/A</div>
      }
      return (
        <div className="text-sm text-slate-600">
          {autoscaling.min ?? '-'} - {autoscaling.max ?? '-'}
        </div>
      )
    },
  },
]

export const getColumnsForType = (componentType: 'webapp' | 'worker' | 'cron') => {
  const baseColumns = getBaseColumns()
  const webappColumns = getWebappColumns()
  const cronColumns = getCronColumns()
  const workerColumns = getWorkerColumns()

  if (componentType === 'webapp') {
    return [
      baseColumns[0], // name
      baseColumns[1], // url
      webappColumns[0], // exposure
      webappColumns[1], // visibility
      baseColumns[2], // cpu
      baseColumns[3], // memory
      webappColumns[2], // autoscaling
      baseColumns[4], // status
    ]
  }
  if (componentType === 'cron') {
    return [
      baseColumns[0], // name
      cronColumns[0], // command
      cronColumns[1], // schedule
      baseColumns[2], // cpu
      baseColumns[3], // memory
      baseColumns[4], // status
    ]
  }
  // Worker
  return [
    baseColumns[0], // name
    baseColumns[2], // cpu
    baseColumns[3], // memory
    workerColumns[0], // autoscaling
    baseColumns[4], // status
  ]
}
