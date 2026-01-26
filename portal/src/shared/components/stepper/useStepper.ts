import { useState } from 'react'

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
