import { z } from 'zod'

export const clusterCreateSchema = z.object({
  name: z.string().min(1, 'Cluster name is required').max(100, 'Name must be less than 100 characters'),
  api_address: z.string().url('Invalid API address URL').min(1, 'API address is required'),
  token: z.string().min(1, 'Token is required'),
  environment_uuid: z.string().uuid('Invalid environment UUID'),
  gateway_namespace: z.string().max(253, 'Namespace must be less than 253 characters').optional().or(z.literal('')),
  gateway_name: z.string().max(253, 'Name must be less than 253 characters').optional().or(z.literal('')),
})

export type ClusterCreateInput = z.infer<typeof clusterCreateSchema>
