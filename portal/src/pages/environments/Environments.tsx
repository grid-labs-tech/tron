import { useState, useEffect, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { X, Trash2, Plus, Settings, Cloud } from 'lucide-react'
import {
  useEnvironments,
  useEnvironment,
  useCreateEnvironment,
  useDeleteEnvironment,
  useUpdateEnvironmentSettings,
  useResetEnvironmentSettings,
} from '../../features/environments'
import { useCrossplaneConfig, useUpdateCrossplaneConfig } from '../../features/crossplane'
import type { EnvironmentCrossplaneConfig } from '../../features/crossplane'
import { useOrganization } from '../../contexts/OrganizationContext'
import type { Environment, EnvironmentCreate, EnvironmentSettingItem } from '../../features/environments'
import { DataTable, Breadcrumbs, PageHeader } from '../../shared/components'

const EMPTY_CROSSPLANE_CONFIG: EnvironmentCrossplaneConfig = {
  enabled: false,
  cluster_uuid: null,
  aws_region: '',
  aws_account_id: '',
  provider_config: '',
}

function Environments() {
  const [isOpen, setIsOpen] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const { selectedOrganizationUuid, isLoading: isLoadingOrg } = useOrganization()
  const queryClient = useQueryClient()

  const { data: environments = [], isLoading } = useEnvironments(selectedOrganizationUuid)
  const createMutation = useCreateEnvironment(selectedOrganizationUuid)
  const deleteMutation = useDeleteEnvironment(selectedOrganizationUuid)
  const updateSettingsMutation = useUpdateEnvironmentSettings(selectedOrganizationUuid)
  const resetSettingsMutation = useResetEnvironmentSettings(selectedOrganizationUuid)

  const [settingsModalOpen, setSettingsModalOpen] = useState(false)
  const [selectedEnvForSettings, setSelectedEnvForSettings] = useState<Environment | null>(null)
  const [settingsSearch, setSettingsSearch] = useState('')
  const [settingsDraft, setSettingsDraft] = useState<EnvironmentSettingItem[]>([])

  const [crossplaneModalOpen, setCrossplaneModalOpen] = useState(false)
  const [selectedEnvForCrossplane, setSelectedEnvForCrossplane] = useState<Environment | null>(null)
  const [crossplaneDraft, setCrossplaneDraft] = useState<EnvironmentCrossplaneConfig>(EMPTY_CROSSPLANE_CONFIG)
  const [crossplaneFormError, setCrossplaneFormError] = useState<string | null>(null)

  const [formData, setFormData] = useState<EnvironmentCreate>({
    name: '',
  })

  useEffect(() => {
    if (createMutation.isSuccess && createMutation.data) {
      setNotification({ type: 'success', message: 'Environment created successfully' })
      setIsOpen(false)
      setFormData({ name: '' })
      setTimeout(() => setNotification(null), 5000)
      createMutation.reset()
    }
  }, [createMutation.isSuccess, createMutation.data, createMutation])

  useEffect(() => {
    if (createMutation.isError) {
      setNotification({
        type: 'error',
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        message: (createMutation.error as any)?.response?.data?.detail || 'Error creating environment',
      })
      setTimeout(() => setNotification(null), 5000)
      createMutation.reset()
    }
  }, [createMutation.isError, createMutation])

  useEffect(() => {
    if (deleteMutation.isSuccess) {
      setNotification({ type: 'success', message: 'Environment deleted successfully' })
      setTimeout(() => setNotification(null), 5000)
      deleteMutation.reset()
    }
  }, [deleteMutation.isSuccess, deleteMutation])

  useEffect(() => {
    if (deleteMutation.isError) {
      setNotification({
        type: 'error',
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        message: (deleteMutation.error as any)?.response?.data?.detail || 'Error deleting environment',
      })
      setTimeout(() => setNotification(null), 5000)
      deleteMutation.reset()
    }
  }, [deleteMutation.isError, deleteMutation])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name) {
      setNotification({ type: 'error', message: 'Name is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }
    createMutation.mutate(formData)
  }

  const handleDelete = (uuid: string) => {
    if (confirm('Are you sure you want to delete this environment?')) {
      deleteMutation.mutate(uuid)
    }
  }

  const openSettingsModal = (env: Environment) => {
    setSelectedEnvForSettings(env)
    setSettingsDraft(env.settings ? [...env.settings] : [])
    setSettingsSearch('')
    setSettingsModalOpen(true)
  }

  const closeSettingsModal = () => {
    setSettingsModalOpen(false)
    setSelectedEnvForSettings(null)
    setSettingsSearch('')
  }

  const updateCrossplaneMutation = useUpdateCrossplaneConfig(selectedOrganizationUuid)
  const { data: envForCrossplane } = useEnvironment(
    selectedOrganizationUuid ?? undefined,
    selectedEnvForCrossplane?.uuid
  )
  const {
    data: loadedCrossplaneConfig,
    isPending: crossplaneConfigPending,
    isError: crossplaneLoadError,
    error: crossplaneLoadErr,
  } = useCrossplaneConfig(
    selectedOrganizationUuid ?? undefined,
    selectedEnvForCrossplane?.uuid
  )
  // Block save until GET finishes — avoids wiping config with EMPTY draft
  const canSaveCrossplane =
    !!loadedCrossplaneConfig && !crossplaneConfigPending && !crossplaneLoadError

  useEffect(() => {
    if (loadedCrossplaneConfig) {
      setCrossplaneDraft(loadedCrossplaneConfig)
      setCrossplaneFormError(null)
    }
  }, [loadedCrossplaneConfig])

  useEffect(() => {
    if (!crossplaneModalOpen || !crossplaneLoadError) return
    const detail =
      (crossplaneLoadErr as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Failed to load Crossplane config'
    setCrossplaneFormError(detail)
  }, [crossplaneModalOpen, crossplaneLoadError, crossplaneLoadErr])

  const availableCrossplaneClusters = envForCrossplane?.clusters ?? []

  const openCrossplaneModal = (env: Environment) => {
    setSelectedEnvForCrossplane(env)
    setCrossplaneFormError(null)
    const cached = queryClient.getQueryData<EnvironmentCrossplaneConfig>([
      'crossplane-config',
      selectedOrganizationUuid,
      env.uuid,
    ])
    setCrossplaneDraft(cached ?? EMPTY_CROSSPLANE_CONFIG)
    setCrossplaneModalOpen(true)
  }

  const closeCrossplaneModal = () => {
    setCrossplaneModalOpen(false)
    setSelectedEnvForCrossplane(null)
    setCrossplaneDraft(EMPTY_CROSSPLANE_CONFIG)
    setCrossplaneFormError(null)
    updateCrossplaneMutation.reset()
  }

  const handleSaveCrossplane = () => {
    if (!selectedEnvForCrossplane || !canSaveCrossplane) return
    setCrossplaneFormError(null)
    updateCrossplaneMutation.mutate(
      { environmentUuid: selectedEnvForCrossplane.uuid, config: crossplaneDraft },
      {
        onSuccess: () => {
          setNotification({ type: 'success', message: 'Crossplane config saved successfully' })
          closeCrossplaneModal()
          setTimeout(() => setNotification(null), 5000)
        },
        onError: (err: unknown) => {
          setCrossplaneFormError(
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
              'Error saving Crossplane config'
          )
        },
      }
    )
  }

  const filteredSettings = useMemo(() => {
    if (!settingsDraft.length) return []
    const q = settingsSearch.trim().toLowerCase()
    if (!q) return settingsDraft
    return settingsDraft.filter(
      (s) =>
        s.key.toLowerCase().includes(q) ||
        (s.description || '').toLowerCase().includes(q)
    )
  }, [settingsDraft, settingsSearch])

  const handleSettingValueChange = (key: string, value: string | number | boolean | string[]) => {
    setSettingsDraft((prev) =>
      prev.map((s) => (s.key === key ? { ...s, value } : s))
    )
  }

  const handleSaveSettings = () => {
    if (!selectedEnvForSettings || !selectedOrganizationUuid) return
    const settingsPayload = Object.fromEntries(
      settingsDraft.map((s) => [s.key, s.value])
    )
    updateSettingsMutation.mutate(
      { environmentUuid: selectedEnvForSettings.uuid, settings: settingsPayload },
      {
        onSuccess: () => {
          setNotification({ type: 'success', message: 'Settings saved successfully' })
          setTimeout(() => setNotification(null), 5000)
          closeSettingsModal()
          updateSettingsMutation.reset()
        },
        onError: (err: unknown) => {
          setNotification({
            type: 'error',
            message: (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error saving settings',
          })
          setTimeout(() => setNotification(null), 5000)
          updateSettingsMutation.reset()
        },
      }
    )
  }

  const handleResetSettings = () => {
    if (!selectedEnvForSettings || !selectedOrganizationUuid) return
    if (!confirm('Reset all settings to default values? This cannot be undone.')) return
    resetSettingsMutation.mutate(selectedEnvForSettings.uuid, {
      onSuccess: (data) => {
        setSettingsDraft(Array.isArray(data) ? [...data] : [])
        setNotification({ type: 'success', message: 'Settings reset to default' })
        setTimeout(() => setNotification(null), 5000)
        resetSettingsMutation.reset()
      },
      onError: (err: unknown) => {
        setNotification({
          type: 'error',
          message: (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error resetting settings',
        })
        setTimeout(() => setNotification(null), 5000)
        resetSettingsMutation.reset()
      },
    })
  }

  if (isLoadingOrg) {
    return (
      <div className="space-y-6">
        <Breadcrumbs
          items={[
            { label: 'Home', path: '/' },
            { label: 'Environments', path: '/environments' },
          ]}
        />
        <div className="flex items-center justify-center p-8">
          <div className="text-slate-600">Loading organizations...</div>
        </div>
      </div>
    )
  }

  if (!selectedOrganizationUuid) {
    return (
      <div className="space-y-6">
        <Breadcrumbs
          items={[
            { label: 'Home', path: '/' },
            { label: 'Environments', path: '/environments' },
          ]}
        />
        <div className="rounded-lg p-4 bg-yellow-50 border border-yellow-200 text-yellow-800">
          <p>No organization found. Please create an organization first.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Environments', path: '/environments' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader title="Environments" description="Manage environments" />
        <button
          onClick={() => {
            setFormData({ name: '' })
            setIsOpen(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-soft hover:shadow-soft-lg transition-all duration-200 text-sm font-medium"
        >
          <Plus size={18} />
          New Environment
        </button>
      </div>

      {notification && (
        <div
          className={`rounded-lg p-4 flex items-center justify-between ${
            notification.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}
        >
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Table */}
      <DataTable<Environment>
        columns={[
          {
            key: 'name',
            label: 'Name',
            render: (env) => (
              <div>
                <div className="text-sm font-medium text-slate-800">{env.name}</div>
                <div className="text-xs text-slate-500 font-mono mt-0.5">{env.uuid}</div>
              </div>
            ),
          },
          {
            key: 'clusters_count',
            label: 'Clusters',
            render: (env) => (
              <div className="text-sm text-slate-600">
                {env.clusters?.length ?? 0}
              </div>
            ),
          },
          {
            key: 'created_at',
            label: 'Created at',
            render: (env) => (
              <div className="text-sm text-slate-600">
                {new Date(env.created_at).toLocaleDateString('pt-BR')}
              </div>
            ),
          },
        ]}
        data={environments}
        isLoading={isLoading}
        emptyMessage="No environments found"
        loadingColor="blue"
        getRowKey={(env) => env.uuid}
        actions={(env) => [
          {
            label: 'Settings',
            icon: <Settings size={14} />,
            onClick: () => openSettingsModal(env),
          },
          {
            label: 'Crossplane',
            icon: <Cloud size={14} />,
            onClick: () => openCrossplaneModal(env),
          },
          {
            label: 'Delete',
            icon: <Trash2 size={14} />,
            onClick: () => handleDelete(env.uuid),
            variant: 'danger',
          },
        ]}
      />

      {/* Settings modal */}
      {settingsModalOpen && selectedEnvForSettings && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-2xl w-full border border-slate-200/60 animate-zoom-in max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50 shrink-0">
              <h2 className="text-lg font-semibold text-slate-800">
                Settings — {selectedEnvForSettings.name}
              </h2>
              <button
                onClick={closeSettingsModal}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-5 space-y-4 flex-1 min-h-0 flex flex-col">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Search by key or description</label>
                <input
                  type="text"
                  value={settingsSearch}
                  onChange={(e) => setSettingsSearch(e.target.value)}
                  placeholder="Filter settings..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                />
              </div>
              <div className="border border-slate-200 rounded-lg overflow-auto flex-1 min-h-0">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 sticky top-0">
                    <tr>
                      <th className="text-left py-2 px-3 font-medium text-slate-700">Key</th>
                      <th className="text-left py-2 px-3 font-medium text-slate-700">Description</th>
                      <th className="text-left py-2 px-3 font-medium text-slate-700">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSettings.map((item) => (
                      <tr key={item.key} className="border-t border-slate-100">
                        <td className="py-2 px-3 font-mono text-slate-800">{item.key}</td>
                        <td className="py-2 px-3 text-slate-600 max-w-[200px] break-words whitespace-normal" title={item.description}>
                          {item.description || '—'}
                        </td>
                        <td className="py-2 px-3">
                          {item.type === 'boolean' ? (
                            <label className="inline-flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={item.value === true}
                                onChange={(e) =>
                                  handleSettingValueChange(item.key, e.target.checked)
                                }
                                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                              />
                              <span className="text-slate-600 text-xs">
                                {item.value === true ? 'Enabled' : 'Disabled'}
                              </span>
                            </label>
                          ) : item.type === 'number' && (
                            <input
                              type="number"
                              value={typeof item.value === 'number' ? item.value : ''}
                              onChange={(e) =>
                                handleSettingValueChange(
                                  item.key,
                                  e.target.value === '' ? 0 : Number(e.target.value)
                                )
                              }
                              className="w-full max-w-[120px] px-2 py-1 border border-slate-300 rounded text-sm"
                            />
                          )}
                          {item.type === 'list' && (
                            <input
                              type="text"
                              value={Array.isArray(item.value) ? item.value.join(', ') : String(item.value)}
                              onChange={(e) =>
                                handleSettingValueChange(
                                  item.key,
                                  e.target.value ? e.target.value.split(',').map((x) => x.trim()) : []
                                )
                              }
                              className="w-full max-w-[180px] px-2 py-1 border border-slate-300 rounded text-sm"
                            />
                          )}
                          {item.type !== 'number' && item.type !== 'list' && item.type !== 'boolean' && (
                            <input
                              type="text"
                              value={String(item.value)}
                              onChange={(e) =>
                                handleSettingValueChange(item.key, e.target.value)
                              }
                              className="w-full max-w-[180px] px-2 py-1 border border-slate-300 rounded text-sm"
                            />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredSettings.length === 0 && (
                  <div className="p-4 text-center text-slate-500 text-sm">No settings match the search.</div>
                )}
              </div>
              <div className="flex justify-end gap-2.5 pt-2 shrink-0">
                <button
                  type="button"
                  onClick={handleResetSettings}
                  disabled={resetSettingsMutation.isPending}
                  className="px-4 py-2 text-amber-700 bg-amber-100 rounded-lg hover:bg-amber-200 transition-colors text-sm font-medium disabled:opacity-50"
                >
                  {resetSettingsMutation.isPending ? 'Resetting...' : 'Reset to default'}
                </button>
                <button
                  type="button"
                  onClick={closeSettingsModal}
                  className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveSettings}
                  disabled={updateSettingsMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
                >
                  {updateSettingsMutation.isPending ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {crossplaneModalOpen && selectedEnvForCrossplane && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-md w-full border border-slate-200/60 animate-zoom-in">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800">
                Crossplane — {selectedEnvForCrossplane.name}
              </h2>
              <button
                onClick={closeCrossplaneModal}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-5 space-y-4">
              {crossplaneFormError ? (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 flex items-start justify-between gap-2">
                  <span>{crossplaneFormError}</span>
                  <button
                    type="button"
                    onClick={() => setCrossplaneFormError(null)}
                    className="text-red-500 hover:text-red-700 shrink-0"
                  >
                    <X size={14} />
                  </button>
                </div>
              ) : null}
              {!canSaveCrossplane && !crossplaneLoadError ? (
                <p className="text-sm text-slate-500">Loading Crossplane config…</p>
              ) : null}
              <fieldset
                disabled={!canSaveCrossplane}
                className="space-y-4 disabled:opacity-60"
              >
              <label className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={crossplaneDraft.enabled}
                  onChange={(e) =>
                    setCrossplaneDraft({ ...crossplaneDraft, enabled: e.target.checked })
                  }
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                Enable Crossplane for this environment
              </label>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Cluster</label>
                <select
                  value={crossplaneDraft.cluster_uuid ?? ''}
                  onChange={(e) =>
                    setCrossplaneDraft({
                      ...crossplaneDraft,
                      cluster_uuid: e.target.value || null,
                    })
                  }
                  disabled={!crossplaneDraft.enabled}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm disabled:bg-slate-100 disabled:text-slate-400"
                >
                  <option value="">
                    {crossplaneDraft.enabled
                      ? availableCrossplaneClusters.length
                        ? 'Select cluster'
                        : 'No clusters in this environment'
                      : 'Enable Crossplane first'}
                  </option>
                  {availableCrossplaneClusters.map((cluster) => (
                    <option key={cluster.uuid} value={cluster.uuid}>
                      {cluster.name}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-slate-500">
                  Clusters in this environment. Crossplane must be healthy on the
                  selected cluster (verified on save).
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">AWS region</label>
                <input
                  type="text"
                  value={crossplaneDraft.aws_region}
                  onChange={(e) =>
                    setCrossplaneDraft({ ...crossplaneDraft, aws_region: e.target.value })
                  }
                  disabled={!crossplaneDraft.enabled}
                  placeholder="us-east-1"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm disabled:bg-slate-100 disabled:text-slate-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  AWS account ID
                </label>
                <input
                  type="text"
                  value={crossplaneDraft.aws_account_id}
                  onChange={(e) =>
                    setCrossplaneDraft({ ...crossplaneDraft, aws_account_id: e.target.value })
                  }
                  disabled={!crossplaneDraft.enabled}
                  placeholder="000000000000"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm disabled:bg-slate-100 disabled:text-slate-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Provider config
                </label>
                <input
                  type="text"
                  value={crossplaneDraft.provider_config}
                  onChange={(e) =>
                    setCrossplaneDraft({ ...crossplaneDraft, provider_config: e.target.value })
                  }
                  disabled={!crossplaneDraft.enabled}
                  placeholder="default"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm disabled:bg-slate-100 disabled:text-slate-400"
                />
                <p className="mt-1 text-xs text-slate-500">
                  ClusterProviderConfig name used by Crossplane in this environment.
                </p>
              </div>
              </fieldset>
              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={closeCrossplaneModal}
                  className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveCrossplane}
                  disabled={!canSaveCrossplane || updateCrossplaneMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
                >
                  {updateCrossplaneMutation.isPending
                    ? 'Saving...'
                    : !canSaveCrossplane && !crossplaneLoadError
                      ? 'Loading...'
                      : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-md w-full border border-slate-200/60 animate-zoom-in">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800">New Environment</h2>
              <button
                onClick={() => setIsOpen(false)}
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
                  placeholder="production"
                  required
                />
              </div>
              <div className="flex justify-end gap-2.5 pt-3">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Environments
