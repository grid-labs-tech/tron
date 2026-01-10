import { z } from 'zod'

export const instanceCreateSchema = z.object({
  application_uuid: z.string().uuid('Invalid application UUID'),
  environment_uuid: z.string().uuid('Invalid environment UUID'),
  image: z.string().min(1, 'Image is required'),
  version: z.string().min(1, 'Version is required'),
  enabled: z.boolean().optional().default(true),
})

// Schema for validating instance form before application is created (without application_uuid)
export const instanceFormSchema = z.object({
  environment_uuid: z.string().uuid('Invalid environment UUID'),
  image: z.string().min(1, 'Image is required'),
  version: z.string().min(1, 'Version is required'),
  enabled: z.boolean().optional().default(true),
})

export type InstanceCreateInput = z.infer<typeof instanceCreateSchema>
export type InstanceFormInput = z.infer<typeof instanceFormSchema>