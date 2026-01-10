import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useWebappComponent } from '../../features/components'
import { useInstance } from '../../features/instances'
import { useApplication } from '../../features/applications'
import { useWebappDetail } from './hooks/useWebappDetail'
import { PodsTable } from './components/PodsTable'
import { PodLogsModal } from './components/PodLogsModal'
import { PodConsoleModal } from './components/PodConsoleModal'
import { Breadcrumbs, PageHeader } from '../../shared/components'

function WebappDetail() {
  const { uuid: applicationUuid, instanceUuid, componentUuid } = useParams<{
    uuid: string
    instanceUuid: string
    componentUuid: string
  }>()

  const { data: component } = useWebappComponent(componentUuid)
  const { data: instance } = useInstance(instanceUuid)
  const { data: application } = useApplication(applicationUuid)

  const [refreshInterval, setRefreshInterval] = useState<number>(5000) // Default: 5 seconds

  const {
    pods,
    isLoadingPods,
    selectedPod,
    isLogsModalOpen,
    isConsoleModalOpen,
    isLiveTail,
    podLogs,
    isLoadingLogs,
    commandOutput,
    currentCommand,
    isExecuting,
    handleViewLogs,
    handleOpenConsole,
    handleCloseLogsModal,
    handleCloseConsoleModal,
    handleDeletePod,
    handleCommandSubmit,
    handleCommandChange,
    setIsLiveTail,
    handleKeyDown,
  } = useWebappDetail(componentUuid, refreshInterval)

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

      <PodsTable
        pods={pods}
        isLoading={isLoadingPods}
        onViewLogs={handleViewLogs}
        onOpenConsole={handleOpenConsole}
        onDeletePod={handleDeletePod}
      />

      <PodLogsModal
        isOpen={isLogsModalOpen}
        podName={selectedPod}
        logs={podLogs}
        isLoading={isLoadingLogs}
        isLiveTail={isLiveTail}
        onClose={handleCloseLogsModal}
        onToggleLiveTail={setIsLiveTail}
      />

      <PodConsoleModal
        isOpen={isConsoleModalOpen}
        podName={selectedPod}
        commandOutput={commandOutput}
        currentCommand={currentCommand}
        isExecuting={isExecuting}
        onClose={handleCloseConsoleModal}
        onCommandChange={handleCommandChange}
        onCommandSubmit={handleCommandSubmit}
        onKeyDown={handleKeyDown}
      />
    </div>
  )
}

export default WebappDetail

