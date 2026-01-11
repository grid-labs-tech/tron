interface CommandInputProps {
  command: string | null
  onChange: (command: string | null) => void
  isArray?: boolean
}

export function CommandInput({ command, onChange, isArray = false }: CommandInputProps) {
  if (isArray) {
    const commandArray = Array.isArray(command) ? command : []

    const addCommand = () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onChange([...commandArray, ''] as any)
    }

    const updateCommand = (index: number, value: string) => {
      const updated = commandArray.map((cmd, i) => (i === index ? value : cmd))
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onChange(updated as any)
    }

    const removeCommand = (index: number) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onChange(commandArray.filter((_, i) => i !== index) as any)
    }

    return (
      <div className="border border-slate-200 rounded-lg p-3 bg-white">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-xs font-semibold text-slate-700">Command</h5>
          <button
            type="button"
            onClick={addCommand}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            + Add
          </button>
        </div>
        {commandArray.map((cmd, cmdIndex) => (
          <div key={cmdIndex} className="mb-2 flex gap-2">
            <input
              type="text"
              value={cmd}
              onChange={(e) => updateCommand(cmdIndex, e.target.value)}
              placeholder="Command argument"
              className="flex-1 px-2 py-1 border border-slate-300 rounded text-xs font-mono focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
            <button
              type="button"
              onClick={() => removeCommand(cmdIndex)}
              className="px-2 py-1 text-red-600 hover:bg-red-50 rounded text-xs"
            >
              ×
            </button>
          </div>
        ))}
        {commandArray.length === 0 && (
          <p className="text-xs text-slate-400">
            No command specified. The default image command will be used.
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <h5 className="text-xs font-semibold text-slate-700 mb-2">Command (optional)</h5>
      <p className="text-xs text-slate-500 mb-2">
        Override the default container command. Enter the full command as a string (e.g., "python app.py --port 8080").
      </p>
      <textarea
        value={command || ''}
        onChange={(e) => {
          const value = e.target.value.trim()
          onChange(value.length > 0 ? value : null)
        }}
        placeholder='python app.py --port 8080'
        rows={3}
        className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs font-mono focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
      />
      <p className="text-xs text-slate-400 mt-1">
        Leave empty to use the default image command. The command will be parsed and split into arguments automatically.
      </p>
    </div>
  )
}

