import { useState, useEffect } from 'react'
import { useWebappPods, useDeleteWebappPod, useWebappPodLogs, useExecWebappPodCommand } from '../../../features/components'
import type { PodCommandResponse } from '../../../features/components'

export const useWebappDetail = (componentUuid: string | undefined, refreshInterval: number) => {
  const [selectedPod, setSelectedPod] = useState<string | undefined>(undefined)
  const [isLogsModalOpen, setIsLogsModalOpen] = useState(false)
  const [isConsoleModalOpen, setIsConsoleModalOpen] = useState(false)
  const [isLiveTail, setIsLiveTail] = useState(true)
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [commandOutput, setCommandOutput] = useState<Array<{ command: string; response: PodCommandResponse; timestamp: Date }>>([])
  const [currentCommand, setCurrentCommand] = useState('')

  const { data: pods = [], isLoading: isLoadingPods } = useWebappPods(
    componentUuid,
    refreshInterval > 0 ? refreshInterval : false
  )

  const deletePodMutation = useDeleteWebappPod()
  const execCommandMutation = useExecWebappPodCommand()

  const { data: podLogs, isLoading: isLoadingLogs } = useWebappPodLogs(
    componentUuid,
    selectedPod,
    undefined,
    100,
    isLiveTail && isLogsModalOpen ? 2000 : false
  )

  // Handle exec command success
  useEffect(() => {
    if (execCommandMutation.isSuccess && execCommandMutation.data) {
      const commandStr = execCommandMutation.variables?.command.join(' ') || ''
      setCommandHistory((prev) => [...prev, commandStr])
      setCommandOutput((prev) => [
        ...prev,
        {
          command: commandStr,
          response: execCommandMutation.data!,
          timestamp: new Date(),
        },
      ])
      setCurrentCommand('')
      setTimeout(() => {
        // Scroll will be handled by PodConsoleModal
      }, 100)
      execCommandMutation.reset()
    }
  }, [execCommandMutation.isSuccess, execCommandMutation.data, execCommandMutation])

  const handleViewLogs = (podName: string) => {
    setSelectedPod(podName)
    setIsLogsModalOpen(true)
  }

  const handleOpenConsole = (podName: string) => {
    setSelectedPod(podName)
    setIsConsoleModalOpen(true)
    setCommandOutput([])
    setCommandHistory([])
    setCurrentCommand('')
  }

  const handleCloseLogsModal = () => {
    setIsLogsModalOpen(false)
    setSelectedPod(undefined)
    setIsLiveTail(true)
  }

  const handleCloseConsoleModal = () => {
    setIsConsoleModalOpen(false)
    setSelectedPod(undefined)
    setCommandOutput([])
    setCommandHistory([])
    setCurrentCommand('')
  }

  const handleDeletePod = (podName: string) => {
    if (confirm(`Are you sure you want to delete pod "${podName}"?`) && componentUuid) {
      deletePodMutation.mutate({ uuid: componentUuid, podName })
    }
  }

  const handleCommandSubmit = (command: string) => {
    if (!command.trim() || !selectedPod || !componentUuid) return

    const commandParts = command.trim().split(/\s+/)
    execCommandMutation.mutate({
      uuid: componentUuid,
      podName: selectedPod,
      command: commandParts,
    })
  }

  const handleCommandChange = (command: string) => {
    setCurrentCommand(command)
    setHistoryIndex(-1)
  }

  // Handle command history navigation
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

  return {
    pods,
    isLoadingPods,
    selectedPod,
    isLogsModalOpen,
    isConsoleModalOpen,
    isLiveTail,
    podLogs: podLogs?.logs,
    isLoadingLogs,
    commandOutput,
    currentCommand,
    isExecuting: execCommandMutation.isPending,
    handleViewLogs,
    handleOpenConsole,
    handleCloseLogsModal,
    handleCloseConsoleModal,
    handleDeletePod,
    handleCommandSubmit,
    handleCommandChange,
    setIsLiveTail,
    handleKeyDown,
  }
}
