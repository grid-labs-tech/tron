import { z } from 'zod'

export const validateForm = <T>(schema: z.ZodSchema<T>, data: unknown): { success: boolean; data?: T; errors?: Record<string, string> } => {
  try {
    const validatedData = schema.parse(data)
    return { success: true, data: validatedData }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors: Record<string, string> = {}
      // ZodError always has the issues property (not errors)
      if (error.issues && Array.isArray(error.issues)) {
        error.issues.forEach((issue) => {
          // Check if there's a path and if it's not empty
          if (issue.path && Array.isArray(issue.path) && issue.path.length > 0) {
            const fieldName = issue.path[0] as string
            // If error already exists for this field, keep the first or concatenate
            if (!errors[fieldName]) {
              errors[fieldName] = issue.message
            }
          } else {
            // If there's no path or path is empty, use _form as fallback
            // If _form already exists, concatenate or keep the first
            if (!errors._form) {
              errors._form = issue.message
            }
          }
        })
      }
      // If there are no specific errors, add generic error
      if (Object.keys(errors).length === 0) {
        errors._form = 'Validation failed'
      }
      return { success: false, errors }
    }
    console.error('Validation error:', error)
    return { success: false, errors: { _form: 'Validation failed' } }
  }
}

export const getFieldError = (errors: Record<string, string> | undefined, field: string): string | undefined => {
  return errors?.[field]
}
