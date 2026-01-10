import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { X, Trash2, Plus, FileCode, Edit, ChevronDown, ChevronRight, Settings, Copy, Check } from 'lucide-react'
import { useTemplates, useCreateTemplate, useUpdateTemplate, useDeleteTemplate, useComponentTemplateConfigs } from '../../features/templates'
import { componentTemplateConfigsApi } from '../../features/templates/api'
import type {
  Template,
  TemplateCreate,
  TemplateUpdate,
  ComponentTemplateConfig,
  ComponentTemplateConfigCreate,
  ComponentTemplateConfigUpdate,
} from '../../features/templates'
import { DataTable, Breadcrumbs, PageHeader } from '../../shared/components'

// Variáveis disponíveis para templates webapp
const WEBAPP_VARIABLES = {
  application: {
    component_name: 'string',
    component_uuid: 'string',
    component_type: 'string (webapp|worker|cron)',
    application_name: 'string',
    application_uuid: 'string',
    environment: 'string',
    environment_uuid: 'string',
    image: 'string',
    version: 'string',
    visibility: 'string',
    url: 'string | null',
    enabled: 'boolean',
    settings: {
      cpu: 'number',
      memory: 'number',
      cpu_scaling_threshold: 'number',
      memory_scaling_threshold: 'number',
      autoscaling: {
        min: 'number',
        max: 'number',
      },
      custom_metrics: {
        enabled: 'boolean',
        path: 'string',
        port: 'number',
      },
      exposure: {
        type: 'string (http|tcp|udp)',
        port: 'number',
        visibility: 'string (cluster|private|public)',
      },
      envs: 'array<{key: string, value: string}>',
      command: 'string | null (will be parsed into array)',
      healthcheck: {
        path: 'string',
        protocol: 'string (http|tcp)',
        port: 'number',
        timeout: 'number',
        interval: 'number',
        initial_interval: 'number',
        failure_threshold: 'number',
      },
    },
  },
  environment: {
    // Chaves dinâmicas baseadas nas settings do environment
    // Exemplo: { "key1": "value1", "key2": "value2", ... }
    '[key: string]': 'string',
  },
  cluster: {
    gateway: {
      reference: {
        namespace: 'string',
        name: 'string',
      },
    },
  },
}

function Templates() {
  const [isOpen, setIsOpen] = useState(false)
  const [isConfigOpen, setIsConfigOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'templates' | 'configs'>('templates')
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
  const [editingConfig, setEditingConfig] = useState<ComponentTemplateConfig | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [selectedComponentType, setSelectedComponentType] = useState<string>('webapp')
  const [showVariables, setShowVariables] = useState(true)
  const [copiedPath, setCopiedPath] = useState<string | null>(null)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const { data: templates = [], isLoading } = useTemplates()
  const { data: configs = [], isLoading: isLoadingConfigs } = useComponentTemplateConfigs(selectedComponentType)
  const createMutation = useCreateTemplate()
  const updateMutation = useUpdateTemplate()
  const deleteMutation = useDeleteTemplate()

  const [configFormData, setConfigFormData] = useState<ComponentTemplateConfigCreate>({
    component_type: 'webapp',
    template_uuid: '',
    render_order: 0,
    enabled: true,
  })

  const [formData, setFormData] = useState<TemplateCreate>({
    name: '',
    description: '',
    category: 'webapp',
    content: '',
    variables_schema: '',
  })

  useEffect(() => {
    if (createMutation.isSuccess) {
      setNotification({ type: 'success', message: 'Template created successfully' })
      setIsOpen(false)
      setEditingTemplate(null)
      setFormData({ name: '', description: '', category: 'webapp', content: '', variables_schema: '' })
      setTimeout(() => setNotification(null), 5000)
      createMutation.reset()
    }
  }, [createMutation.isSuccess])

  useEffect(() => {
    if (createMutation.isError) {
      setNotification({
        type: 'error',
        message: (createMutation.error as any)?.response?.data?.detail || 'Error creating template',
      })
      setTimeout(() => setNotification(null), 5000)
      createMutation.reset()
    }
  }, [createMutation.isError])

  useEffect(() => {
    if (updateMutation.isSuccess) {
      setNotification({ type: 'success', message: 'Template updated successfully' })
      setIsOpen(false)
      setEditingTemplate(null)
      setSelectedTemplate(null)
      setFormData({ name: '', description: '', category: 'webapp', content: '', variables_schema: '' })
      setTimeout(() => setNotification(null), 5000)
      updateMutation.reset()
    }
  }, [updateMutation.isSuccess])

  useEffect(() => {
    if (updateMutation.isError) {
      setNotification({
        type: 'error',
        message: (updateMutation.error as any)?.response?.data?.detail || 'Error updating template',
      })
      setTimeout(() => setNotification(null), 5000)
      updateMutation.reset()
    }
  }, [updateMutation.isError])

  useEffect(() => {
    if (deleteMutation.isSuccess) {
      setNotification({ type: 'success', message: 'Template deleted successfully' })
      setSelectedTemplate(null)
      setTimeout(() => setNotification(null), 5000)
      deleteMutation.reset()
    }
  }, [deleteMutation.isSuccess])

  useEffect(() => {
    if (deleteMutation.isError) {
      setNotification({
        type: 'error',
        message: (deleteMutation.error as any)?.response?.data?.detail || 'Error deleting template',
      })
      setTimeout(() => setNotification(null), 5000)
      deleteMutation.reset()
    }
  }, [deleteMutation.isError])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.category || !formData.content) {
      setNotification({ type: 'error', message: 'Name, Category and Content are required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    if (editingTemplate) {
      const updateData: TemplateUpdate = {
        name: formData.name,
        description: formData.description || undefined,
        content: formData.content,
        variables_schema: formData.variables_schema || undefined,
      }
      updateMutation.mutate({ uuid: editingTemplate.uuid, data: updateData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (template: Template) => {
    setEditingTemplate(template)
    setFormData({
      name: template.name,
      description: template.description || '',
      category: template.category,
      content: template.content,
      variables_schema: template.variables_schema || '',
    })
    setIsOpen(true)
  }

  const handleView = (template: Template) => {
    setSelectedTemplate(template)
  }

  const handleCloseModal = () => {
    setIsOpen(false)
    setEditingTemplate(null)
    setFormData({ name: '', description: '', category: 'webapp', content: '', variables_schema: '' })
  }

  const handleDelete = (uuid: string) => {
    if (confirm('Are you sure you want to delete this template?')) {
      deleteMutation.mutate(uuid)
    }
  }

  // Config mutations - using direct API calls since hooks not created yet
  const createConfigMutation = useMutation({
    mutationFn: componentTemplateConfigsApi.create,
    onSuccess: () => {
      setNotification({ type: 'success', message: 'Template configuration created successfully' })
      setIsConfigOpen(false)
      setConfigFormData({
        component_type: selectedComponentType,
        template_uuid: '',
        render_order: 0,
        enabled: true,
      })
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error creating template configuration',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const updateConfigMutation = useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: ComponentTemplateConfigUpdate }) =>
      componentTemplateConfigsApi.update(uuid, data),
    onSuccess: () => {
      setNotification({ type: 'success', message: 'Template configuration updated successfully' })
      setIsConfigOpen(false)
      setEditingConfig(null)
      setConfigFormData({
        component_type: selectedComponentType,
        template_uuid: '',
        render_order: 0,
        enabled: true,
      })
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error updating template configuration',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const deleteConfigMutation = useMutation({
    mutationFn: componentTemplateConfigsApi.delete,
    onSuccess: () => {
      setNotification({ type: 'success', message: 'Template configuration deleted successfully' })
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error deleting template configuration',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const handleConfigSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!configFormData.template_uuid) {
      setNotification({ type: 'error', message: 'Template is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }
    if (editingConfig) {
      updateConfigMutation.mutate({
        uuid: editingConfig.uuid,
        data: {
          render_order: configFormData.render_order,
          enabled: configFormData.enabled,
        },
      })
    } else {
      createConfigMutation.mutate(configFormData)
    }
  }

  const handleDeleteConfig = (uuid: string) => {
    if (confirm('Are you sure you want to delete this template configuration?')) {
      deleteConfigMutation.mutate(uuid)
    }
  }

  const handleCloseConfigModal = () => {
    setIsConfigOpen(false)
    setEditingConfig(null)
    setConfigFormData({
      component_type: selectedComponentType,
      template_uuid: '',
      render_order: 0,
      enabled: true,
    })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedPath(text)
    setTimeout(() => setCopiedPath(null), 2000)
  }

  const renderVariablesTree = (obj: any, prefix = '', level = 0) => {
    return Object.entries(obj).map(([key, value]) => {
      const fullPath = prefix ? `${prefix}.${key}` : key
      const isObject = typeof value === 'object' && value !== null && !Array.isArray(value)
      const isCopied = copiedPath === fullPath

      return (
        <div key={fullPath} className={level > 0 ? 'ml-6 border-l-2 border-slate-200 pl-3' : ''}>
          <div className="group flex items-center gap-2 py-1.5 hover:bg-slate-50 rounded px-2 -ml-2 transition-colors">
            <button
              onClick={() => copyToClipboard(fullPath)}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-slate-200 rounded"
              title="Copy path"
            >
              {isCopied ? (
                <Check size={14} className="text-green-600" />
              ) : (
                <Copy size={14} className="text-slate-500" />
              )}
            </button>
            <div className="flex-1 min-w-0">
              <span className="text-slate-800 font-mono text-sm font-medium">{key}</span>
              {typeof value === 'string' && (
                <span className="ml-2 text-slate-500 text-xs">: {value}</span>
              )}
            </div>
          </div>
          {isObject && (
            <div className="mt-1">
              {renderVariablesTree(value, fullPath, level + 1)}
            </div>
          )}
        </div>
      )
    })
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Templates', path: '/templates' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader title="Templates" description="Manage Jinja2 templates" />
        <div className="flex items-center gap-2">
          {activeTab === 'templates' && (
            <button
              onClick={() => {
                setEditingTemplate(null)
                setFormData({
                  name: '',
                  description: '',
                  category: 'webapp',
                  content: '',
                  variables_schema: '',
                })
                setIsOpen(true)
              }}
              className="btn-primary flex items-center gap-2"
            >
              <Plus size={18} />
              <span>New Template</span>
            </button>
          )}
          {activeTab === 'configs' && (
            <button
              onClick={() => {
                setConfigFormData({
                  component_type: selectedComponentType,
                  template_uuid: '',
                  render_order: configs.length,
                  enabled: true,
                })
                setIsConfigOpen(true)
              }}
              className="btn-primary flex items-center gap-2"
            >
              <Plus size={18} />
              <span>Add Template to Component</span>
            </button>
          )}
        </div>
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

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('templates')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'templates'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Templates
          </button>
          <button
            onClick={() => setActiveTab('configs')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'configs'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Settings size={16} />
              Component Configurations
            </div>
          </button>
        </nav>
      </div>

      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Table */}
          <div className="lg:col-span-2">
            <DataTable<Template>
            columns={[
              {
                key: 'name',
                label: 'Name',
                render: (template) => (
                  <div>
                    <div className="text-sm font-medium text-slate-800">{template.name}</div>
                    {template.description && (
                      <div className="text-xs text-slate-500 mt-0.5">{template.description}</div>
                    )}
                  </div>
                ),
              },
              {
                key: 'category',
                label: 'Category',
                render: (template) => (
                  <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-700">
                    {template.category}
                  </span>
                ),
              },
            ]}
            data={templates}
            isLoading={isLoading}
            emptyMessage="No templates found"
            loadingColor="blue"
            getRowKey={(template) => template.uuid}
            actions={(template) => [
              {
                label: 'View',
                icon: <FileCode size={14} />,
                onClick: () => handleView(template),
                variant: 'default',
              },
              {
                label: 'Edit',
                icon: <Edit size={14} />,
                onClick: () => handleEdit(template),
                variant: 'default',
              },
              {
                label: 'Delete',
                icon: <Trash2 size={14} />,
                onClick: () => handleDelete(template.uuid),
                variant: 'danger',
              },
            ]}
          />
        </div>

        {/* Variables Panel */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-soft border border-slate-200/60 overflow-hidden">
            <button
              onClick={() => setShowVariables(!showVariables)}
              className="flex items-center justify-between w-full text-left p-4 hover:bg-slate-50 transition-colors"
            >
              <div>
                <h3 className="text-sm font-semibold text-slate-800">Available Variables</h3>
                <p className="text-xs text-slate-500 mt-0.5">Click to copy variable paths</p>
              </div>
              {showVariables ? <ChevronDown size={18} className="text-slate-400" /> : <ChevronRight size={18} className="text-slate-400" />}
            </button>
            {showVariables && (
              <div className="border-t border-slate-200/60 p-4 max-h-[600px] overflow-y-auto">
                <div className="space-y-1">
                  {renderVariablesTree(WEBAPP_VARIABLES)}
                </div>
                <div className="mt-4 pt-4 border-t border-slate-200/60">
                  <p className="text-xs text-slate-500">
                    <strong className="text-slate-700">Tip:</strong> Hover over any variable and click the copy icon to copy its path to your clipboard.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      )}

      {activeTab === 'configs' && (
        <div className="space-y-4">
          {/* Component Type Selector */}
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-slate-700">Component Type:</label>
            <select
              value={selectedComponentType}
              onChange={(e) => setSelectedComponentType(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all bg-white text-sm"
            >
              <option value="webapp">webapp</option>
              <option value="cron">cron</option>
              <option value="worker">worker</option>
            </select>
          </div>

          {/* Configurations Table */}
          <DataTable<ComponentTemplateConfig>
            columns={[
              {
                key: 'render_order',
                label: 'Order',
                render: (config) => (
                  <div className="text-sm font-medium text-slate-800">{config.render_order}</div>
                ),
              },
              {
                key: 'template_name',
                label: 'Template',
                render: (config) => (
                  <div>
                    <div className="text-sm font-medium text-slate-800">
                      {config.template_name || 'Unknown'}
                    </div>
                  </div>
                ),
              },
              {
                key: 'enabled',
                label: 'Status',
                render: (config) => (
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                      config.enabled
                        ? 'bg-green-100 text-green-700'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {config.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                ),
              },
            ]}
            data={configs}
            isLoading={isLoadingConfigs}
            emptyMessage={`No template configurations found for ${selectedComponentType}`}
            loadingColor="blue"
            getRowKey={(config) => config.uuid}
            actions={(config) => [
              {
                label: 'Edit',
                icon: <Edit size={14} />,
                onClick: () => {
                  setEditingConfig(config)
                  setConfigFormData({
                    component_type: config.component_type,
                    template_uuid: config.template_uuid,
                    render_order: config.render_order,
                    enabled: config.enabled,
                  })
                  setIsConfigOpen(true)
                },
                variant: 'default',
              },
              {
                label: 'Delete',
                icon: <Trash2 size={14} />,
                onClick: () => handleDeleteConfig(config.uuid),
                variant: 'danger',
              },
            ]}
          />
        </div>
      )}

      {/* Create/Edit Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-4xl w-full border border-slate-200/60 animate-zoom-in max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingTemplate ? 'Edit Template' : 'New Template'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                    placeholder="Deployment Template"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all bg-white text-sm"
                    required
                    disabled={!!editingTemplate}
                  >
                    <option value="webapp">webapp</option>
                    <option value="cron">cron</option>
                    <option value="worker">worker</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                  placeholder="Template description"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Content</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm font-mono"
                  rows={15}
                  placeholder="apiVersion: apps/v1&#10;kind: Deployment&#10;..."
                  required
                />
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
                  {editingTemplate
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

      {/* View Template Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-4xl w-full border border-slate-200/60 animate-zoom-in max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <div>
                <h2 className="text-lg font-semibold text-slate-800">{selectedTemplate.name}</h2>
                {selectedTemplate.description && (
                  <p className="text-sm text-slate-500 mt-1">{selectedTemplate.description}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedTemplate(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-5 overflow-y-auto flex-1">
              <div className="mb-4 flex gap-2">
                <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-700">
                  {selectedTemplate.category}
                </span>
              </div>
              <pre className="bg-slate-50 rounded-lg p-4 text-xs font-mono text-slate-800 overflow-x-auto">
                {selectedTemplate.content}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Config Create/Edit Modal */}
      {isConfigOpen && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-md w-full border border-slate-200/60 animate-zoom-in">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingConfig ? 'Edit Template Configuration' : 'Add Template to Component'}
              </h2>
              <button
                onClick={handleCloseConfigModal}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleConfigSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Component Type</label>
                <select
                  value={configFormData.component_type}
                  onChange={(e) =>
                    setConfigFormData({ ...configFormData, component_type: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all bg-white text-sm"
                  required
                >
                  <option value="webapp">webapp</option>
                  <option value="cron">cron</option>
                  <option value="worker">worker</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Template</label>
                <select
                  value={configFormData.template_uuid}
                  onChange={(e) =>
                    setConfigFormData({ ...configFormData, template_uuid: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all bg-white text-sm"
                  required
                  disabled={!!editingConfig}
                >
                  <option value="">Select a template</option>
                  {templates
                    .filter((t) => t.category === configFormData.component_type)
                    .map((template) => (
                      <option key={template.uuid} value={template.uuid}>
                        {template.name}
                      </option>
                    ))}
                </select>
                {editingConfig && (
                  <p className="mt-1 text-xs text-slate-500">Template cannot be changed after creation.</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Render Order</label>
                <input
                  type="number"
                  value={configFormData.render_order}
                  onChange={(e) =>
                    setConfigFormData({ ...configFormData, render_order: parseInt(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
                  placeholder="0"
                  min="0"
                  required
                />
                <p className="mt-1 text-xs text-slate-500">
                  Templates are rendered in ascending order (0 first, then 1, 2, etc.)
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={configFormData.enabled}
                  onChange={(e) =>
                    setConfigFormData({ ...configFormData, enabled: e.target.checked })
                  }
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="enabled" className="text-sm font-medium text-slate-700">
                  Enabled
                </label>
              </div>
              <div className="flex justify-end gap-2.5 pt-3">
                <button
                  type="button"
                  onClick={handleCloseConfigModal}
                  className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createConfigMutation.isPending || updateConfigMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
                >
                  {editingConfig
                    ? updateConfigMutation.isPending
                      ? 'Saving...'
                      : 'Save'
                    : createConfigMutation.isPending
                      ? 'Creating...'
                      : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Templates

