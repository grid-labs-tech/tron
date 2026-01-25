import { useNavigate } from 'react-router-dom'
import { Trash2, Plus, Layers, Server } from 'lucide-react'
import { useApplications, useDeleteApplication } from '../../features/applications'
import { useInstances } from '../../features/instances'
import type { Application } from '../../features/applications'
import type { Instance } from '../../features/instances'
import { DataTable, Breadcrumbs, PageHeader } from '../../shared/components'

function Applications() {
  const navigate = useNavigate()

  const { data: applications = [], isLoading } = useApplications()
  const { data: instances = [] } = useInstances()
  const deleteMutation = useDeleteApplication()

  const handleDelete = (uuid: string) => {
    if (confirm('Are you sure you want to delete this application?')) {
      deleteMutation.mutate(uuid)
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Applications', path: '/applications' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader title="Applications" description="Manage applications" />
        <button
          onClick={() => navigate('/applications/new')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={18} />
          <span>New Application</span>
        </button>
      </div>

      {/* Table */}
      <DataTable<Application>
        columns={[
          {
            key: 'name',
            label: 'Name',
            render: (application) => (
              <div>
                <div className="text-sm font-medium text-slate-800">{application.name}</div>
                <small className="text-xs text-slate-500">{application.uuid}</small>
              </div>
            ),
          },
          {
            key: 'repository',
            label: 'Repository',
            render: (application) => (
              <div className="text-sm text-slate-600">{application.repository || '-'}</div>
            ),
          },
          {
            key: 'status',
            label: 'Status',
            render: (application) => (
              <div>
                {application.enabled ? (
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
          {
            key: 'created_at',
            label: 'Creation Date',
            render: (application) => (
              <div className="text-sm text-slate-600">
                {new Date(application.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            ),
          },
          {
            key: 'updated_at',
            label: 'Update Date',
            render: (application) => (
              <div className="text-sm text-slate-600">
                {new Date(application.updated_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            ),
          },
        ]}
        data={applications}
        isLoading={isLoading}
        emptyMessage="No applications found"
        loadingColor="blue"
        getRowKey={(application) => application.uuid}
        actions={(application) => {
          // Filter instances of this application
          const applicationInstances = instances.filter(
            (instance: Instance) => instance.application.uuid === application.uuid
          )

          // Build actions array
          const actions = [
            {
              label: 'New Instance',
              icon: <Layers size={14} />,
              onClick: () => navigate(`/applications/${application.uuid}/instances/new`),
              variant: 'default' as const,
            },
          ]

          // Add existing instances
          if (applicationInstances.length > 0) {
            applicationInstances.forEach((instance: Instance) => {
              actions.push({
                label: `Instance: ${instance.environment.name}`,
                icon: <Server size={14} />,
                onClick: () => navigate(`/applications/${application.uuid}/instances/${instance.uuid}/components`),
                variant: 'default' as const,
              })
            })
          }

          // Add delete action at the end
          actions.push({
            label: 'Delete',
            icon: <Trash2 size={14} />,
            onClick: () => handleDelete(application.uuid),
            variant: 'danger',
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          } as any)

          return actions
        }}
      />
    </div>
  )
}

export default Applications
