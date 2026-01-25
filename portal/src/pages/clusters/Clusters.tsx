import { useState, useEffect } from 'react'
import { X, Trash2, Plus, Info, Edit, CheckCircle, XCircle } from 'lucide-react'
import { useClusters, useCreateCluster, useUpdateCluster, useDeleteCluster } from '../../features/clusters'
import { useEnvironments } from '../../features/environments'
import type { Cluster, ClusterCreate } from '../../features/clusters'
import { DataTable, Breadcrumbs, PageHeader } from '../../shared/components'

function Clusters() {
  const [isOpen, setIsOpen] = useState(false)
  const [editingCluster, setEditingCluster] = useState<Cluster | null>(null)
  const [statusModal, setStatusModal] = useState<{ code: string; message: string } | null>(null)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const { data: clusters = [], isLoading } = useClusters()
  const { data: environments = [] } = useEnvironments()

  const [formData, setFormData] = useState<ClusterCreate>({
    name: '',
    api_address: '',
    token: '',
    environment_uuid: '',
    gateway_namespace: '',
    gateway_name: '',
  })

  const createMutation = useCreateCluster()
  const updateMutation = useUpdateCluster()
  const deleteMutation = useDeleteCluster()

  // Handle success/error callbacks
  useEffect(() => {
    if (createMutation.isSuccess && createMutation.data) {
      setNotification({ type: 'success', message: 'Cluster created successfully' })
      setIsOpen(false)
      setEditingCluster(null)
      setFormData({ name: '', api_address: '', token: '', environment_uuid: '', gateway_namespace: '', gateway_name: '' })
      setTimeout(() => setNotification(null), 5000)
      createMutation.reset()
    }
  }, [createMutation.isSuccess, createMutation.data, createMutation])

  useEffect(() => {
    if (createMutation.isError) {
      setNotification({
        type: 'error',
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        message: (createMutation.error as any)?.response?.data?.detail || 'Error creating cluster',
      })
      setTimeout(() => setNotification(null), 5000)
      createMutation.reset()
    }
  }, [createMutation.isError, createMutation])

  useEffect(() => {
    if (updateMutation.isSuccess && updateMutation.data) {
      setNotification({ type: 'success', message: 'Cluster updated successfully' })
      setIsOpen(false)
      setEditingCluster(null)
      setFormData({ name: '', api_address: '', token: '', environment_uuid: '', gateway_namespace: '', gateway_name: '' })
      setTimeout(() => setNotification(null), 5000)
      updateMutation.reset()
    }
  }, [updateMutation.isSuccess, updateMutation.data, updateMutation])

  useEffect(() => {
    if (updateMutation.isError) {
      setNotification({
        type: 'error',
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        message: (updateMutation.error as any)?.response?.data?.detail || 'Error updating cluster',
      })
      setTimeout(() => setNotification(null), 5000)
      updateMutation.reset()
    }
  }, [updateMutation.isError, updateMutation])

  useEffect(() => {
    if (deleteMutation.isSuccess) {
      setNotification({ type: 'success', message: 'Cluster deleted successfully' })
      setTimeout(() => setNotification(null), 5000)
      deleteMutation.reset()
    }
  }, [deleteMutation.isSuccess, deleteMutation])

  useEffect(() => {
    if (deleteMutation.isError) {
      setNotification({
        type: 'error',
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        message: (deleteMutation.error as any)?.response?.data?.detail || 'Error deleting cluster',
      })
      setTimeout(() => setNotification(null), 5000)
      deleteMutation.reset()
    }
  }, [deleteMutation.isError, deleteMutation])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.api_address || !formData.environment_uuid) {
      setNotification({ type: 'error', message: 'Name, API Address and Environment are required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    if (!formData.token) {
      setNotification({ type: 'error', message: 'Token is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    if (editingCluster) {
      // Always send environment_uuid and token in update
      const updateData: ClusterCreate = {
        name: formData.name,
        api_address: formData.api_address,
        token: formData.token,
        environment_uuid: formData.environment_uuid,
        gateway_namespace: formData.gateway_namespace || undefined,
        gateway_name: formData.gateway_name || undefined,
      }
      updateMutation.mutate({ uuid: editingCluster.uuid, data: updateData })
    } else {
      const createData: ClusterCreate = {
        ...formData,
        gateway_namespace: formData.gateway_namespace || undefined,
        gateway_name: formData.gateway_name || undefined,
      }
      createMutation.mutate(createData)
    }
  }

  const handleEdit = (cluster: Cluster) => {
    setEditingCluster(cluster)
    const environmentUuid = cluster.environment?.uuid || cluster.environment_uuid
    setFormData({
      name: cluster.name,
      api_address: cluster.api_address,
      token: '', // Token is not returned by API for security
      environment_uuid: environmentUuid,
      gateway_namespace: cluster.gateway?.reference?.namespace || '',
      gateway_name: cluster.gateway?.reference?.name || '',
    })
    setIsOpen(true)
  }

  const handleCloseModal = () => {
    setIsOpen(false)
    setEditingCluster(null)
    setFormData({ name: '', api_address: '', token: '', environment_uuid: '' })
  }

  const handleDelete = (uuid: string) => {
    if (confirm('Are you sure you want to delete this cluster?')) {
      deleteMutation.mutate(uuid)
    }
  }

  const handleStatusClick = (cluster: Cluster) => {
    const statusLower = cluster.detail?.status?.toLowerCase()
    if (
      cluster.detail?.message &&
      (statusLower === 'error' || statusLower === 'failed' || statusLower === 'unhealthy')
    ) {
      setStatusModal({
        code: cluster.detail.message.code,
        message: cluster.detail.message.message,
      })
    }
  }

  const getStatusColor = (status?: string) => {
    if (!status) return 'bg-slate-100 text-slate-700'
    const statusLower = status.toLowerCase()
    if (statusLower === 'active' || statusLower === 'ok' || statusLower === 'healthy') {
      return 'bg-green-100 text-green-700'
    }
    if (statusLower === 'error' || statusLower === 'failed' || statusLower === 'unhealthy') {
      return 'bg-red-100 text-red-700'
    }
    if (statusLower === 'warning' || statusLower === 'pending') {
      return 'bg-yellow-100 text-yellow-700'
    }
    return 'bg-slate-100 text-slate-700'
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Clusters', path: '/clusters' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader title="Clusters" description="Manage Kubernetes clusters" />
        <button
          onClick={() => {
            setEditingCluster(null)
            setFormData({ name: '', api_address: '', token: '', environment_uuid: '', gateway_namespace: '', gateway_name: '' })
            setIsOpen(true)
          }}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={18} />
          <span>New Cluster</span>
        </button>
      </div>

      {notification && (
        <div
          className={`rounded-lg p-4 flex items-center justify-between ${
            notification.type === 'success'
              ? 'bg-success/10 border border-success/20 text-success'
              : 'bg-error/10 border border-error/20 text-error'
          }`}
        >
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Table */}
      <DataTable<Cluster>
        columns={[
          {
            key: 'name',
            label: 'Name',
            render: (cluster) => (
              <div>
                <div className="text-sm font-medium text-slate-800">{cluster.name}</div>
                <small className="text-xs text-slate-500">{cluster.uuid}</small>
                    </div>
            ),
          },
          {
            key: 'environment',
            label: 'Environment',
            render: (cluster) => (
              <div>
                {cluster.environment ? (
                  <>
                    <div className="text-sm text-slate-800 font-medium">{cluster.environment.name}</div>
                    <small className="text-xs text-slate-500">{cluster.environment.uuid}</small>
                  </>
                ) : (
                  <div className="text-sm text-slate-400">-</div>
                )}
              </div>
            ),
          },
          {
            key: 'status',
            label: 'Status',
            render: (cluster) => {
              const status = cluster.detail?.status || 'N/A'
              const statusLower = status.toLowerCase()
              const isErrorStatus =
                statusLower === 'error' || statusLower === 'failed' || statusLower === 'unhealthy'
              const hasMessage = !!cluster.detail?.message

              return (
                      <button
                  onClick={() => isErrorStatus && hasMessage && handleStatusClick(cluster)}
                  disabled={!isErrorStatus || !hasMessage}
                  className={`
                    inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md
                    transition-colors
                    ${getStatusColor(status)}
                    ${isErrorStatus && hasMessage ? 'cursor-pointer hover:opacity-80' : 'cursor-default'}
                  `}
                >
                  {status}
                  {isErrorStatus && hasMessage && <Info size={12} />}
                      </button>
              )
            },
          },
          {
            key: 'gateway_api',
            label: 'Gateway API',
            render: (cluster) => {
              const gatewayApi = cluster.gateway?.api
              const gatewayApiEnabled = gatewayApi?.enabled ?? false
              const gatewayResources = gatewayApi?.resources ?? []

              return (
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    {gatewayApiEnabled ? (
                      <>
                        <CheckCircle size={16} className="text-green-600" />
                        <span className="text-sm text-green-700 font-medium">Available</span>
                      </>
                    ) : (
                      <>
                        <XCircle size={16} className="text-slate-400" />
                        <span className="text-sm text-slate-500">Not Available</span>
                      </>
                    )}
                  </div>
                  {gatewayApiEnabled && gatewayResources.length > 0 && (
                    <div className="text-xs text-slate-600 ml-6">
                      Resources: {gatewayResources.join(', ')}
                    </div>
                  )}
                </div>
              )
            },
          },
        ]}
        data={clusters}
        isLoading={isLoading}
        emptyMessage="No clusters found"
        loadingColor="blue"
        getRowKey={(cluster) => cluster.uuid}
        actions={(cluster) => [
          {
            label: 'Edit',
            icon: <Edit size={14} />,
            onClick: () => handleEdit(cluster),
            variant: 'default',
          },
          {
            label: 'Delete',
            icon: <Trash2 size={14} />,
            onClick: () => handleDelete(cluster.uuid),
            variant: 'danger',
          },
        ]}
      />

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-md w-full border border-slate-200/60 animate-zoom-in">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingCluster ? 'Edit Cluster' : 'New Cluster'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                  placeholder="meu-cluster"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">API Address</label>
                <input
                  type="text"
                  value={formData.api_address}
                  onChange={(e) => setFormData({ ...formData, api_address: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                  placeholder="https://kubernetes.example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Token</label>
                <input
                  type="password"
                  value={formData.token}
                  onChange={(e) => setFormData({ ...formData, token: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                  placeholder="ServiceAccount token"
                  required
                />
                {editingCluster && (
                  <p className="mt-1 text-xs text-slate-500">
                    Enter the token again. If you don't want to change it, use the same current token.
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Environment</label>
                <select
                  value={formData.environment_uuid}
                  onChange={(e) => setFormData({ ...formData, environment_uuid: e.target.value })}
                  className={`w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all bg-white text-sm
                    ${editingCluster ? 'bg-slate-100 cursor-not-allowed opacity-80' : ''}
                  `}
                  required
                  disabled={!!editingCluster}
                >
                  <option value="">Select an environment</option>
                  {environments.map((env) => (
                    <option key={env.uuid} value={env.uuid}>
                      {env.name}
                    </option>
                  ))}
                </select>
                {editingCluster && (
                  <p className="mt-1 text-xs text-slate-500">
                    Environment cannot be changed after creation.
                  </p>
                )}
              </div>

              {/* Gateway Configuration (Optional) */}
              <div className="border-t border-slate-200 pt-4 mt-4">
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="text-sm font-medium text-slate-700">Gateway Configuration</h3>
                  <span className="text-xs text-slate-400">(Optional)</span>
                </div>
                <p className="text-xs text-slate-500 mb-3">
                  Leave empty to auto-detect the Gateway. Specify values to use a specific Gateway when multiple controllers are installed.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">Namespace</label>
                    <input
                      type="text"
                      value={formData.gateway_namespace || ''}
                      onChange={(e) => setFormData({ ...formData, gateway_namespace: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                      placeholder="kube-system"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">Gateway Name</label>
                    <input
                      type="text"
                      value={formData.gateway_name || ''}
                      onChange={(e) => setFormData({ ...formData, gateway_name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                      placeholder="gateway"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-3">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
                >
                  {editingCluster
                    ? updateMutation.isPending
                      ? 'Saving...'
                      : 'Save'
                    : createMutation.isPending
                      ? 'Creating...'
                      : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Status Detail Modal */}
      {statusModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-md w-full border border-slate-200/60 animate-zoom-in">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800">Status Details</h2>
              <button
                onClick={() => setStatusModal(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Code</label>
                <div className="px-3 py-2 bg-slate-50 rounded-lg text-sm text-slate-800 font-mono">
                  {statusModal.code}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Message</label>
                <div className="px-3 py-2 bg-slate-50 rounded-lg text-sm text-slate-800">
                  {statusModal.message}
                </div>
              </div>
              <div className="flex justify-end pt-3">
                <button
                  type="button"
                  onClick={() => setStatusModal(null)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Clusters
