import { z } from 'zod'

export const componentCreateSchema = z.object({
  name: z.string().min(1, 'Component name is required'),
  type: z.enum(['webapp', 'worker', 'cron']),
  url: z.string().nullable().optional(),
  visibility: z.enum(['public', 'private', 'cluster']).default('private'),
  enabled: z.boolean().default(true),
  settings: z.record(z.string(), z.any()).nullable().optional(),
}).superRefine((data, ctx) => {
  // URL is required only if type is 'webapp' AND visibility is not 'cluster'
  if (data.type === 'webapp') {
    const settings = data.settings as any
    const exposureType = settings?.exposure?.type || 'http'
    const exposureVisibility = settings?.exposure?.visibility || 'cluster'
    if (exposureType === 'http' && exposureVisibility !== 'cluster' && !data.url) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Webapp components with HTTP exposure type and visibility \'public\' or \'private\' must have a URL',
        path: ['url'],
      })
    }
  }

  // Cron components must have a schedule
  if (data.type === 'cron' && data.settings) {
    const settings = data.settings as any
    if ('schedule' in settings && !settings.schedule) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Cron components must have a schedule',
        path: ['settings', 'schedule'],
      })
    }
  }
})

export type ComponentCreateInput = z.infer<typeof componentCreateSchema>
