import { useState, useRef, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, FileText, X, Terminal } from 'lucide-react'
import { applicationComponentsApi, instancesApi, applicationsApi } from '../../services/api'
import { Breadcrumbs } from '../../components/Breadcrumbs'
import { PageHeader } from '../../components/PageHeader'
import DataTable from '../../components/DataTable'
import type { Pod, PodCommandResponse } from '../../types'

function WebappDetail() {
  const { uuid: applicationUuid, instanceUuid, componentUuid } = useParams<{
    uuid: string
    instanceUuid: string
    componentUuid: string
  }>()

  const { data: component } = useQuery({
    queryKey: ['webapp', componentUuid],
    queryFn: () => applicationComponentsApi.get(componentUuid!),
    enabled: !!componentUuid,
  })

  const { data: instance } = useQuery({
    queryKey: ['instances', instanceUuid],
    queryFn: () => instancesApi.get(instanceUuid!),
    enabled: !!instanceUuid,
  })

  const { data: application } = useQuery({
    queryKey: ['application', applicationUuid],
    queryFn: () => applicationsApi.get(applicationUuid!),
    enabled: !!applicationUuid,
  })

  const queryClient = useQueryClient()

  const [refreshInterval, setRefreshInterval] = useState<number>(5000) // Default: 5 seconds

  const { data: pods = [], isLoading: isLoadingPods } = useQuery({
    queryKey: ['webapp-pods', componentUuid],
    queryFn: () => applicationComponentsApi.getPods(componentUuid!),
    enabled: !!componentUuid,
    refetchInterval: refreshInterval > 0 ? refreshInterval : false, // Desabilita se for 0
  })

  const [selectedPod, setSelectedPod] = useState<string | null>(null)
  const [isLogsModalOpen, setIsLogsModalOpen] = useState(false)
  const [isConsoleModalOpen, setIsConsoleModalOpen] = useState(false)
  const [isLiveTail, setIsLiveTail] = useState(true)
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [commandOutput, setCommandOutput] = useState<Array<{ command: string; response: PodCommandResponse; timestamp: Date }>>([])
  const [currentCommand, setCurrentCommand] = useState('')
  const logsContainerRef = useRef<HTMLPreElement>(null)
  const terminalOutputRef = useRef<HTMLDivElement>(null)
  const commandInputRef = useRef<HTMLInputElement>(null)

  const deletePodMutation = useMutation({
    mutationFn: (podName: string) => applicationComponentsApi.deletePod(componentUuid!, podName),
    onSuccess: () => {
      // Invalidar a query para recarregar a lista de pods
      queryClient.invalidateQueries({ queryKey: ['webapp-pods', componentUuid] })
    },
  })

  const execCommandMutation = useMutation({
    mutationFn: (command: string[]) => {
      if (!selectedPod) throw new Error('No pod selected')
      return applicationComponentsApi.execPodCommand(componentUuid!, selectedPod, command)
    },
    onSuccess: (data, variables) => {
      const commandStr = variables.join(' ')
      setCommandHistory((prev) => [...prev, commandStr])
      setCommandOutput((prev) => [
        ...prev,
        {
          command: commandStr,
          response: data,
          timestamp: new Date(),
        },
      ])
      setCurrentCommand('')
      // Scroll para o final após um pequeno delay
      setTimeout(() => {
        if (terminalOutputRef.current) {
          terminalOutputRef.current.scrollTop = terminalOutputRef.current.scrollHeight
        }
      }, 100)
    },
  })

  const { data: podLogs, isLoading: isLoadingLogs } = useQuery({
    queryKey: ['webapp-pod-logs', componentUuid, selectedPod],
    queryFn: () => applicationComponentsApi.getPodLogs(componentUuid!, selectedPod!),
    enabled: !!selectedPod && isLogsModalOpen,
    refetchInterval: isLiveTail ? 2000 : false, // Atualizar a cada 2 segundos quando livetail estiver ativo
  })

  // Scroll automático para o final quando os logs mudarem ou quando o modal abrir
  useEffect(() => {
    if (isLogsModalOpen && logsContainerRef.current) {
      // Pequeno delay para garantir que o conteúdo foi renderizado
      setTimeout(() => {
        if (logsContainerRef.current) {
          logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
        }
      }, 100)
    }
  }, [podLogs?.logs, isLogsModalOpen, isLiveTail])

  // Scroll automático quando livetail estiver ativo e novos logs chegarem
  useEffect(() => {
    if (isLiveTail && logsContainerRef.current && podLogs?.logs) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
    }
  }, [podLogs?.logs, isLiveTail])

  // Focar no input quando o modal de console abrir
  useEffect(() => {
    if (isConsoleModalOpen && commandInputRef.current) {
      commandInputRef.current.focus()
    }
  }, [isConsoleModalOpen])

  // Scroll automático quando novos comandos são executados
  useEffect(() => {
    if (terminalOutputRef.current) {
      terminalOutputRef.current.scrollTop = terminalOutputRef.current.scrollHeight
    }
  }, [commandOutput])

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentCommand.trim() || !selectedPod) return

    const commandParts = currentCommand.trim().split(/\s+/)
    execCommandMutation.mutate(commandParts)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp' && commandHistory.length > 0) {
      e.preventDefault()
      const newIndex = historyIndex < 0 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1)
      setHistoryIndex(newIndex)
      setCurrentCommand(commandHistory[newIndex])
    } else if (e.key === 'ArrowDown' && historyIndex >= 0) {
      e.preventDefault()
      const newIndex = historyIndex + 1
      if (newIndex >= commandHistory.length) {
        setHistoryIndex(-1)
        setCurrentCommand('')
      } else {
        setHistoryIndex(newIndex)
        setCurrentCommand(commandHistory[newIndex])
      }
    }
  }

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

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Applications', path: '/applications' },
          { label: application?.name || 'Application' },
          { label: instance?.environment.name || 'Environment', path: `/applications/${applicationUuid}/instances/${instanceUuid}/components` },
          { label: 'Components', path: `/applications/${applicationUuid}/instances/${instanceUuid}/components` },
          { label: component?.name || 'Webapp' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader
          title={component?.name || 'Webapp Details'}
          description="Pods running in Kubernetes"
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
              <option value={2000}>2 seconds</option>
              <option value={5000}>5 seconds</option>
              <option value={10000}>10 seconds</option>
              <option value={30000}>30 seconds</option>
              <option value={60000}>1 minute</option>
            </select>
          </label>
        </div>
      </div>

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
        isLoading={isLoadingPods}
        emptyMessage="No pods found"
        loadingColor="blue"
        getRowKey={(pod) => pod.name}
        actions={(pod) => [
          {
            label: 'Logs',
            icon: <FileText size={14} />,
            onClick: () => {
              setSelectedPod(pod.name)
              setIsLogsModalOpen(true)
            },
            variant: 'default' as const,
          },
          {
            label: 'Console',
            icon: <Terminal size={14} />,
            onClick: () => {
              setSelectedPod(pod.name)
              setIsConsoleModalOpen(true)
              setCommandOutput([])
              setCommandHistory([])
            },
            variant: 'default' as const,
          },
          {
            label: 'Delete',
            icon: <Trash2 size={14} />,
            onClick: () => {
              if (confirm(`Are you sure you want to delete pod "${pod.name}"?`)) {
                deletePodMutation.mutate(pod.name)
              }
            },
            variant: 'danger' as const,
          },
        ]}
      />

      {/* Modal de Logs */}
      {isLogsModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-neutral-200">
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-neutral-900">Pod Logs</h2>
                <p className="text-sm text-neutral-600 mt-1">{selectedPod}</p>
              </div>
              <div className="flex items-center gap-4">
                {/* Toggle Live Tail */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isLiveTail}
                    onChange={(e) => setIsLiveTail(e.target.checked)}
                    className="w-4 h-4 text-primary-600 bg-neutral-100 border-neutral-300 rounded focus:ring-primary-500 focus:ring-2"
                  />
                  <span className="text-sm font-medium text-neutral-700">Live Tail</span>
                </label>
                <button
                  onClick={() => {
                    setIsLogsModalOpen(false)
                    setSelectedPod(null)
                    setIsLiveTail(true) // Reset para true quando fechar
                  }}
                  className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
                >
                  <X size={20} className="text-neutral-600" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden p-6">
              {isLoadingLogs ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : podLogs ? (
                <pre
                  ref={logsContainerRef}
                  className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-auto text-sm font-mono whitespace-pre-wrap h-full"
                  style={{ maxHeight: 'calc(90vh - 200px)' }}
                >
                  {podLogs.logs || 'No logs available'}
                </pre>
              ) : (
                <div className="text-center py-12 text-slate-500">No logs available</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal de Console/Terminal */}
      {isConsoleModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-900 rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-700">
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-white">Terminal</h2>
                <p className="text-sm text-slate-400 mt-1">{selectedPod}</p>
              </div>
              <button
                onClick={() => {
                  setIsConsoleModalOpen(false)
                  setSelectedPod(null)
                  setCommandOutput([])
                  setCommandHistory([])
                  setCurrentCommand('')
                }}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <X size={20} className="text-slate-300" />
              </button>
            </div>

            {/* Terminal Output */}
            <div
              ref={terminalOutputRef}
              className="flex-1 overflow-auto p-4 font-mono text-sm text-green-400 bg-black"
              style={{ minHeight: '400px', maxHeight: 'calc(90vh - 200px)' }}
            >
              <div className="text-slate-400 mb-2">
                # Pod Console - Type commands below
              </div>
              {commandOutput.length === 0 && (
                <div className="text-slate-500 mb-4">
                  <div>$ No commands executed yet</div>
                  <div className="mt-2 text-xs">Try: ls, pwd, whoami, ps aux, etc.</div>
                </div>
              )}
              {commandOutput.map((item, idx) => (
                <div key={idx} className="mb-4">
                  <div className="text-blue-400 mb-1">
                    $ {item.command}
                  </div>
                  {item.response.stdout && (
                    <div className="text-green-400 whitespace-pre-wrap mb-1">
                      {item.response.stdout}
                    </div>
                  )}
                  {item.response.stderr && (
                    <div className="text-red-400 whitespace-pre-wrap mb-1">
                      {item.response.stderr}
                    </div>
                  )}
                  {item.response.return_code !== 0 && (
                    <div className="text-red-500 text-xs">
                      Exit code: {item.response.return_code}
                    </div>
                  )}
                </div>
              ))}
              {execCommandMutation.isPending && (
                <div className="text-yellow-400">
                  $ Executing command...
                </div>
              )}
            </div>

            {/* Command Input */}
            <div className="border-t border-slate-700 p-4">
              <form onSubmit={handleCommandSubmit} className="flex items-center gap-2">
                <span className="text-green-400 font-mono">$</span>
                <input
                  ref={commandInputRef}
                  type="text"
                  value={currentCommand}
                  onChange={(e) => {
                    setCurrentCommand(e.target.value)
                    setHistoryIndex(-1)
                  }}
                  onKeyDown={handleKeyDown}
                  disabled={execCommandMutation.isPending}
                  className="flex-1 bg-slate-800 text-white px-3 py-2 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
                  placeholder="Enter command... (Use ↑↓ for history)"
                />
                <button
                  type="submit"
                  disabled={!currentCommand.trim() || execCommandMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Execute
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default WebappDetail

