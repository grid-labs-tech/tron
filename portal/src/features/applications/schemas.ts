import { z } from 'zod'

export const applicationCreateSchema = z.object({
  name: z.string().min(1, 'Application name is required').max(100, 'Name must be less than 100 characters'),
  repository: z.union([
    z.string().url('Invalid repository URL'),
    z.literal(''),
  ]).nullish(),
  enabled: z.boolean().optional().default(true),
})

export type ApplicationCreateInput = z.infer<typeof applicationCreateSchema>
