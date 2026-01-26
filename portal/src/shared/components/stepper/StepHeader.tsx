import { Check, ChevronUp, ChevronDown } from 'lucide-react'
import type { StepStatus } from './types'

export interface StepHeaderProps {
  number: number
  title: string
  status: StepStatus
  summary?: string
  onClick?: () => void
  isClickable?: boolean
}

export function StepHeader({ number, title, status, summary, onClick, isClickable }: StepHeaderProps) {
  const isActive = status === 'active'
  const isCompleted = status === 'completed'
  
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!isClickable}
      className={`w-full flex items-start gap-4 p-4 text-left transition-colors ${
        isClickable ? 'cursor-pointer hover:bg-slate-50' : 'cursor-default'
      } ${isActive ? 'bg-white' : ''}`}
    >
      {/* Step number/icon */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
        isCompleted 
          ? 'bg-blue-600 text-white' 
          : isActive 
            ? 'bg-blue-600 text-white'
            : 'bg-slate-200 text-slate-500'
      }`}>
        {isCompleted ? <Check size={16} /> : number}
      </div>
      
      {/* Step title and summary */}
      <div className="flex-1 min-w-0">
        <h3 className={`text-base font-semibold ${
          isActive ? 'text-slate-900' : isCompleted ? 'text-slate-700' : 'text-slate-400'
        }`}>
          {title}
        </h3>
        {isCompleted && summary && (
          <p className="text-sm text-slate-500 mt-0.5 truncate">{summary}</p>
        )}
        {!isActive && !isCompleted && (
          <p className="text-sm text-slate-400 mt-0.5">Complete the previous step to continue</p>
        )}
      </div>
      
      {/* Expand indicator */}
      {isClickable && (
        <div className="flex-shrink-0 text-slate-400">
          {isActive ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      )}
    </button>
  )
}
