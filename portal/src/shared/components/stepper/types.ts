import type { ReactNode } from 'react'

export type StepStatus = 'pending' | 'active' | 'completed'

export interface Step {
  id: number
  title: string
  summary?: string
  content: ReactNode
  validate?: () => boolean
}
