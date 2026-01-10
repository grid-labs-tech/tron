import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('Invalid email address').min(1, 'Email is required'),
  password: z.string().min(1, 'Password is required'),
})

export const registerSchema = z.object({
  email: z.string().email('Invalid email address').min(1, 'Email is required'),
  password: z.string().min(1, 'Password is required'),
  full_name: z.string().max(200, 'Full name must be less than 200 characters').nullable().optional(),
})

export const updateProfileSchema = z.object({
  email: z.string().email('Invalid email address').optional().nullable(),
  full_name: z.string().max(200, 'Full name must be less than 200 characters').nullable().optional(),
  password: z.string().min(1, 'Password is required').optional().nullable(),
  current_password: z.string().min(1, 'Current password is required when changing password').optional().nullable(),
}).refine((data) => {
  // If password is provided, current_password must also be provided
  if (data.password && !data.current_password) {
    return false
  }
  return true
}, {
  message: 'Current password is required to change password',
  path: ['current_password'],
})

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type UpdateProfileInput = z.infer<typeof updateProfileSchema>
