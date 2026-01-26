import { StepHeader } from './StepHeader'
import { getStepStatus, isStepClickable } from './utils'
import type { Step } from './types'

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
