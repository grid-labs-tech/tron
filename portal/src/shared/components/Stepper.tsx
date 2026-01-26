import { useState, ReactNode } from 'react'
import { Check, ChevronUp, ChevronDown } from 'lucide-react'

export type StepStatus = 'pending' | 'active' | 'completed'

export interface Step {
  id: number
  title: string
  summary?: string
  content: ReactNode
  validate?: () => boolean
}

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

// Utility function to determine step status
export function getStepStatus(
  stepId: number,
  currentStep: number,
  completedSteps: number[]
): StepStatus {
  if (currentStep === stepId) return 'active'
  if (completedSteps.includes(stepId)) return 'completed'
  return 'pending'
}

// Utility function to check if step is clickable
export function isStepClickable(
  stepId: number,
  currentStep: number,
  completedSteps: number[]
): boolean {
  return stepId < currentStep || completedSteps.includes(stepId - 1) || stepId === 1
}

export interface StepperProps {
  steps: Step[]
  currentStep: number
  completedSteps: number[]
  onStepChange: (step: number) => void
  onStepComplete: (step: number) => void
  showContinueButton?: boolean
  continueButtonText?: string
}

export function Stepper({ 
  steps, 
  currentStep, 
  completedSteps, 
  onStepChange,
  onStepComplete,
  showContinueButton = true,
  continueButtonText = 'Continue',
}: StepperProps) {
  const handleGoToStep = (step: number) => {
    if (isStepClickable(step, currentStep, completedSteps)) {
      onStepChange(step)
    }
  }

  const continueToNextStep = () => {
    const currentStepConfig = steps.find(s => s.id === currentStep)
    const isValid = currentStepConfig?.validate ? currentStepConfig.validate() : true
    
    if (isValid) {
      onStepComplete(currentStep)
      if (currentStep < steps.length) {
        onStepChange(currentStep + 1)
      }
    }
  }

  return (
    <div className="space-y-0">
      {steps.map((step) => {
        const status = getStepStatus(step.id, currentStep, completedSteps)
        const isActive = status === 'active'
        const clickable = isStepClickable(step.id, currentStep, completedSteps)

        return (
          <div key={step.id} className="border-b border-slate-200 last:border-b-0">
            <StepHeader
              number={step.id}
              title={step.title}
              status={status}
              summary={step.summary}
              onClick={() => handleGoToStep(step.id)}
              isClickable={clickable}
            />
            
            {/* Step content */}
            {isActive && (
              <div className="px-4 pb-6 pt-2">
                <div className="ml-12">
                  {step.content}
                  
                  {/* Continue button */}
                  {showContinueButton && currentStep < steps.length && (
                    <div className="mt-6">
                      <button
                        type="button"
                        onClick={continueToNextStep}
                        className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        {continueButtonText}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// Hook to manage stepper state
export function useStepper(initialStep: number = 1) {
  const [currentStep, setCurrentStep] = useState(initialStep)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])

  const goToStep = (step: number) => {
    setCurrentStep(step)
  }

  const completeStep = (step: number) => {
    if (!completedSteps.includes(step)) {
      setCompletedSteps(prev => [...prev, step])
    }
  }

  const resetStepper = () => {
    setCurrentStep(initialStep)
    setCompletedSteps([])
  }

  const isStepCompleted = (step: number) => completedSteps.includes(step)

  return {
    currentStep,
    completedSteps,
    goToStep,
    completeStep,
    resetStepper,
    isStepCompleted,
  }
}
