import { useRef, useEffect } from 'react'
import { X } from 'lucide-react'

interface PodLogsModalProps {
  isOpen: boolean
  podName: string | null
  logs: string | undefined
  isLoading: boolean
  isLiveTail: boolean
  onClose: () => void
  onToggleLiveTail: (enabled: boolean) => void
}

export const PodLogsModal = ({
  isOpen,
  podName,
  logs,
  isLoading,
  isLiveTail,
  onClose,
  onToggleLiveTail,
}: PodLogsModalProps) => {
  const logsContainerRef = useRef<HTMLPreElement>(null)

  // Auto-scroll to end when logs change or when modal opens
  useEffect(() => {
    if (isOpen && logsContainerRef.current) {
      setTimeout(() => {
        if (logsContainerRef.current) {
          logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
        }
      }, 100)
    }
  }, [logs, isOpen, isLiveTail])

  // Auto-scroll when livetail is active and new logs arrive
  useEffect(() => {
    if (isLiveTail && logsContainerRef.current && logs) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
    }
  }, [logs, isLiveTail])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200">
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-neutral-900">Pod Logs</h2>
            <p className="text-sm text-neutral-600 mt-1">{podName}</p>
          </div>
          <div className="flex items-center gap-4">
            {/* Toggle Live Tail */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isLiveTail}
                onChange={(e) => onToggleLiveTail(e.target.checked)}
                className="w-4 h-4 text-primary-600 bg-neutral-100 border-neutral-300 rounded focus:ring-primary-500 focus:ring-2"
              />
              <span className="text-sm font-medium text-neutral-700">Live Tail</span>
            </label>
            <button
              onClick={onClose}
              className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
            >
              <X size={20} className="text-neutral-600" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : logs ? (
            <pre
              ref={logsContainerRef}
              className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-auto text-sm font-mono whitespace-pre-wrap h-full"
              style={{ maxHeight: 'calc(90vh - 200px)' }}
            >
              {logs || 'No logs available'}
            </pre>
          ) : (
            <div className="text-center py-12 text-slate-500">No logs available</div>
          )}
        </div>
      </div>
    </div>
  )
}
