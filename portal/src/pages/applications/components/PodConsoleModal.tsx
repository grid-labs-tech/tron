import { useRef, useEffect } from 'react'
import { X } from 'lucide-react'
import type { PodCommandResponse } from '../../../features/components'

interface PodConsoleModalProps {
  isOpen: boolean
  podName: string | undefined
  commandOutput: Array<{ command: string; response: PodCommandResponse; timestamp: Date }>
  currentCommand: string
  isExecuting: boolean
  onClose: () => void
  onCommandChange: (command: string) => void
  onCommandSubmit: (command: string) => void
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void
}

export const PodConsoleModal = ({
  isOpen,
  podName,
  commandOutput,
  currentCommand,
  isExecuting,
  onClose,
  onCommandChange,
  onCommandSubmit,
  onKeyDown,
}: PodConsoleModalProps) => {
  const terminalOutputRef = useRef<HTMLDivElement>(null)
  const commandInputRef = useRef<HTMLInputElement>(null)

  // Focar no input quando o modal abrir
  useEffect(() => {
    if (isOpen && commandInputRef.current) {
      commandInputRef.current.focus()
    }
  }, [isOpen])

  // Auto-scroll when new commands are executed
  useEffect(() => {
    if (terminalOutputRef.current) {
      terminalOutputRef.current.scrollTop = terminalOutputRef.current.scrollHeight
    }
  }, [commandOutput])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (currentCommand.trim()) {
      onCommandSubmit(currentCommand.trim())
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-slate-900 rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-white">Terminal</h2>
            <p className="text-sm text-slate-400 mt-1">{podName}</p>
          </div>
          <button
            onClick={onClose}
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
          {isExecuting && (
            <div className="text-yellow-400">
              $ Executing command...
            </div>
          )}
        </div>

        {/* Command Input */}
        <div className="border-t border-slate-700 p-4">
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <span className="text-green-400 font-mono">$</span>
            <input
              ref={commandInputRef}
              type="text"
              value={currentCommand}
              onChange={(e) => onCommandChange(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={isExecuting}
              className="flex-1 bg-slate-800 text-white px-3 py-2 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
              placeholder="Enter command... (Use ↑↓ for history)"
            />
            <button
              type="submit"
              disabled={!currentCommand.trim() || isExecuting}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Execute
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
