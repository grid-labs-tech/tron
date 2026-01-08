import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Trash2, Plus, Key, Edit, Shield, Copy, Check, AlertCircle } from 'lucide-react'
import { tokensApi } from '../../services/api'
import type { ApiToken, ApiTokenCreate, ApiTokenUpdate } from '../../types'
import DataTable from '../../components/DataTable'
import { Breadcrumbs } from '../../components/Breadcrumbs'
import { PageHeader } from '../../components/PageHeader'

function Tokens() {
  const [isOpen, setIsOpen] = useState(false)
  const [editingToken, setEditingToken] = useState<ApiToken | null>(null)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [newToken, setNewToken] = useState<string | null>(null)
  const [copiedToken, setCopiedToken] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: tokens = [], isLoading } = useQuery({
    queryKey: ['tokens', searchTerm],
    queryFn: () => tokensApi.list({ search: searchTerm || undefined }),
  })

  const [formData, setFormData] = useState<ApiTokenCreate & { expires_at?: string | null }>({
    name: '',
    role: 'user',
    expires_at: null,
  })

  const createMutation = useMutation({
    mutationFn: tokensApi.create,
    onSuccess: (response) => {
      setNotification({ type: 'success', message: 'Token created successfully' })
      setNewToken(response.token) // Guardar o token gerado
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      setIsOpen(false)
      setEditingToken(null)
      resetForm()
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error creating token',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: ApiTokenUpdate }) => tokensApi.update(uuid, data),
    onSuccess: () => {
      setNotification({ type: 'success', message: 'Token updated successfully' })
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      setIsOpen(false)
      setEditingToken(null)
      resetForm()
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error updating token',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: tokensApi.delete,
    onSuccess: () => {
      setNotification({ type: 'success', message: 'Token deleted successfully' })
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error deleting token',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const resetForm = () => {
    setFormData({
      name: '',
      role: 'user',
      expires_at: null,
    })
  }

  const handleOpenCreate = () => {
    setEditingToken(null)
    setNewToken(null)
    resetForm()
    setIsOpen(true)
  }

  const handleEdit = (token: ApiToken) => {
    setEditingToken(token)
    setFormData({
      name: token.name,
      role: token.role,
      expires_at: token.expires_at || null,
    })
    setIsOpen(true)
  }

  const handleDelete = (uuid: string) => {
    if (window.confirm('Are you sure you want to delete this token?')) {
      deleteMutation.mutate(uuid)
    }
  }

  const handleCopyToken = async (token: string) => {
    try {
      await navigator.clipboard.writeText(token)
      setCopiedToken(token)
      setTimeout(() => setCopiedToken(null), 2000)
    } catch (err) {
      setNotification({ type: 'error', message: 'Error copying token' })
      setTimeout(() => setNotification(null), 5000)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name) {
      setNotification({ type: 'error', message: 'Name is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    if (editingToken) {
      updateMutation.mutate({ uuid: editingToken.uuid, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const getRoleBadge = (role: string) => {
    const roleConfig = {
      admin: { label: 'Admin', color: 'bg-purple-100 text-purple-700' },
      user: { label: 'User', color: 'bg-blue-100 text-blue-700' },
      viewer: { label: 'Visualizador', color: 'bg-gray-100 text-gray-700' },
    }

    const config = roleConfig[role as keyof typeof roleConfig] || roleConfig.user

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${config.color}`}>
        <Shield size={12} className="mr-1" />
        {config.label}
      </span>
    )
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Tokens', path: '/tokens' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader title="Tokens" description="Manage API tokens for authentication" />
        <button onClick={handleOpenCreate} className="btn-primary flex items-center gap-2">
          <Plus size={18} />
          <span>New Token</span>
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

      {/* Modal de Token Criado */}
      {newToken && (
        <div className="glass-effect-strong rounded-xl p-6 border-2 border-primary-200">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-neutral-800 mb-2">Token Created Successfully!</h3>
              <p className="text-sm text-neutral-600">
                Copy this token now. You won't be able to see it again.
              </p>
            </div>
            <button
              onClick={() => setNewToken(null)}
              className="p-1 text-neutral-400 hover:text-neutral-600"
            >
              <X size={20} />
            </button>
          </div>
          <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
            <div className="flex items-center justify-between gap-2">
              <code className="text-sm font-mono text-neutral-800 break-all flex-1">{newToken}</code>
              <button
                onClick={() => handleCopyToken(newToken)}
                className="btn-secondary flex items-center gap-2 flex-shrink-0"
                title="Copy token"
              >
                {copiedToken === newToken ? (
                  <>
                    <Check size={16} />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={16} />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>
          <div className="mt-4 p-3 bg-warning/10 border border-warning/20 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle size={16} className="text-warning flex-shrink-0 mt-0.5" />
              <p className="text-xs text-warning">
                <strong>Important:</strong> Use this token in the <code className="bg-neutral-100 px-1 rounded">x-tron-token</code> header for API authentication.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="glass-effect-strong rounded-xl p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name..."
              className="input w-full pl-10"
            />
            <Key size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" />
          </div>
        </div>
      </div>

      <div className="glass-effect-strong rounded-2xl shadow-soft-lg overflow-hidden">
        <DataTable<ApiToken>
          columns={[
            {
              key: 'name',
              label: 'Name',
              render: (token) => (
                <div className="flex items-center gap-2">
                  <Key size={16} className="text-neutral-400" />
                  <span className="text-sm font-medium text-neutral-800">{token.name}</span>
                </div>
              ),
            },
            {
              key: 'role',
              label: 'Role',
              render: (token) => getRoleBadge(token.role),
            },
            {
              key: 'is_active',
              label: 'Status',
              render: (token) => (
                <div className="flex items-center gap-2">
                  {token.is_active ? (
                    <span className="text-sm text-success font-medium">Active</span>
                  ) : (
                    <span className="text-sm text-error font-medium">Inactive</span>
                  )}
                </div>
              ),
            },
            {
              key: 'expires_at',
              label: 'Expires at',
              render: (token) => (
                <div className="text-sm text-neutral-600">
                  {formatDate(token.expires_at)}
                </div>
              ),
            },
            {
              key: 'last_used_at',
              label: 'Last used',
              render: (token) => (
                <div className="text-sm text-neutral-600">
                  {formatDate(token.last_used_at)}
                </div>
              ),
            },
            {
              key: 'created_at',
              label: 'Created at',
              render: (token) => (
                <div className="text-sm text-neutral-600">
                  {new Date(token.created_at).toLocaleDateString('pt-BR')}
                </div>
              ),
            },
          ]}
          data={tokens}
          isLoading={isLoading}
          emptyMessage="No tokens found"
          loadingColor="blue"
          getRowKey={(token) => token.uuid}
          actions={(token) => [
            {
              label: 'Edit',
              icon: <Edit size={14} />,
              onClick: () => handleEdit(token),
              variant: 'default' as const,
            },
            {
              label: 'Delete',
              icon: <Trash2 size={14} />,
              onClick: () => handleDelete(token.uuid),
              variant: 'danger' as const,
            },
          ]}
        />
      </div>

      {/* Modal Create/Edit */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-effect-strong rounded-2xl shadow-soft-lg w-full max-w-md p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gradient">
                {editingToken ? 'Edit Token' : 'New Token'}
              </h2>
              <button
                onClick={() => {
                  setIsOpen(false)
                  setEditingToken(null)
                  resetForm()
                }}
                className="p-2 rounded-lg text-neutral-600 hover:bg-neutral-100 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-neutral-700 mb-2">
                  Name *
                </label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  placeholder="Token name"
                  required
                />
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-neutral-700 mb-2">
                  Role
                </label>
                <select
                  id="role"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as any })}
                  className="select w-full"
                >
                  <option value="user">User</option>
                  <option value="admin">Administrator</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>

              {editingToken && (
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active ?? editingToken.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm font-medium text-neutral-700">Active token</span>
                  </label>
                </div>
              )}

              <div>
                <label htmlFor="expires_at" className="block text-sm font-medium text-neutral-700 mb-2">
                  Expiration Date (optional)
                </label>
                <input
                  id="expires_at"
                  type="datetime-local"
                  value={formData.expires_at ? new Date(formData.expires_at).toISOString().slice(0, 16) : ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    expires_at: e.target.value ? new Date(e.target.value).toISOString() : null
                  })}
                  className="input w-full"
                />
              </div>

              <div className="flex items-center justify-end gap-4 pt-4 border-t border-neutral-200">
                <button
                  type="button"
                  onClick={() => {
                    setIsOpen(false)
                    setEditingToken(null)
                    resetForm()
                  }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="btn-primary"
                >
                  {createMutation.isPending || updateMutation.isPending ? (
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Saving...</span>
                    </div>
                  ) : (
                    <span>{editingToken ? 'Save' : 'Create'}</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Tokens

