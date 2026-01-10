import { z } from 'zod'

export const validateForm = <T>(schema: z.ZodSchema<T>, data: unknown): { success: boolean; data?: T; errors?: Record<string, string> } => {
  try {
    const validatedData = schema.parse(data)
    return { success: true, data: validatedData }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors: Record<string, string> = {}
      // ZodError sempre tem a propriedade issues (não errors)
      if (error.issues && Array.isArray(error.issues)) {
        error.issues.forEach((issue) => {
          if (issue.path && Array.isArray(issue.path) && issue.path.length > 0) {
            const fieldName = issue.path[0] as string
            errors[fieldName] = issue.message
          } else {
            // Se não houver path, usar _form como fallback
            errors._form = issue.message
          }
        })
      }
      // Se não houver erros específicos, adicionar erro genérico
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
