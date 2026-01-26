import type { StepStatus } from './types'

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
