import { useState, useEffect } from 'react'

interface ScheduleInputProps {
  schedule: string
  onChange: (schedule: string) => void
}

interface ScheduleOption {
  label: string
  value: string
  description: string
}

const SCHEDULE_OPTIONS: ScheduleOption[] = [
  { label: 'Every minute', value: '* * * * *', description: 'Runs every minute' },
  { label: 'Every 5 minutes', value: '*/5 * * * *', description: 'Runs every 5 minutes' },
  { label: 'Every 15 minutes', value: '*/15 * * * *', description: 'Runs every 15 minutes' },
  { label: 'Every 30 minutes', value: '*/30 * * * *', description: 'Runs every 30 minutes' },
  { label: 'Every hour', value: '0 * * * *', description: 'Runs at the start of every hour' },
  { label: 'Every day at midnight', value: '0 0 * * *', description: 'Runs daily at 00:00' },
  { label: 'Every day at noon', value: '0 12 * * *', description: 'Runs daily at 12:00' },
  { label: 'Every week (Sunday midnight)', value: '0 0 * * 0', description: 'Runs every Sunday at 00:00' },
  { label: 'Every month (1st at midnight)', value: '0 0 1 * *', description: 'Runs on the 1st of every month at 00:00' },
  { label: 'Custom', value: 'CUSTOM', description: 'Enter a custom cron expression' },
]

export function ScheduleInput({ schedule, onChange }: ScheduleInputProps) {
  const [isCustom, setIsCustom] = useState(false)
  const [customValue, setCustomValue] = useState('')

  // Check if current schedule matches any predefined option
  useEffect(() => {
    const matchingOption = SCHEDULE_OPTIONS.find(opt => opt.value === schedule)
    if (matchingOption && matchingOption.value !== 'CUSTOM') {
      setIsCustom(false)
      setCustomValue('')
    } else {
      setIsCustom(true)
      setCustomValue(schedule)
    }
  }, [schedule])

  const handlePresetChange = (value: string) => {
    if (value === 'CUSTOM') {
      setIsCustom(true)
      if (customValue) {
        onChange(customValue)
      }
    } else {
      setIsCustom(false)
      setCustomValue('')
      onChange(value)
    }
  }

  const handleCustomChange = (value: string) => {
    setCustomValue(value)
    onChange(value)
  }

  const selectedPreset = SCHEDULE_OPTIONS.find(opt => opt.value === schedule && opt.value !== 'CUSTOM')
  const selectedValue = isCustom ? 'CUSTOM' : (selectedPreset?.value || '')

  return (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">
        Schedule (Cron Expression) *
      </label>

      <div className="space-y-2">
        <select
          value={selectedValue}
          onChange={(e) => handlePresetChange(e.target.value)}
          className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 bg-white"
        >
          {SCHEDULE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {isCustom && (
          <div>
            <input
              type="text"
              value={customValue}
              onChange={(e) => handleCustomChange(e.target.value)}
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 font-mono"
              placeholder="0 0 * * *"
              required
            />
            <p className="text-xs text-slate-400 mt-1">
              Cron expression format: minute hour day month weekday
            </p>
          </div>
        )}

        {!isCustom && selectedPreset && (
          <p className="text-xs text-slate-500 mt-1">
            {selectedPreset.description} • Expression: <code className="font-mono text-slate-600">{selectedPreset.value}</code>
          </p>
        )}
      </div>
    </div>
  )
}

