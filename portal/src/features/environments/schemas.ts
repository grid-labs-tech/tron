import { z } from 'zod'

export const environmentCreateSchema = z.object({
  name: z.string().min(1, 'Environment name is required').max(100, 'Name must be less than 100 characters'),
})

export type EnvironmentCreateInput = z.infer<typeof environmentCreateSchema>
