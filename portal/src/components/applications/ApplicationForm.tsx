import type { ApplicationCreate } from '../../types'

interface ApplicationFormProps {
  data: ApplicationCreate
  onChange: (data: ApplicationCreate) => void
}

export function ApplicationForm({ data, onChange }: ApplicationFormProps) {
  return (
    <div className="bg-white rounded-xl shadow-soft border border-slate-200/60 p-6">
      <h2 className="text-xl font-semibold text-slate-800 mb-4">Application</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Name *</label>
          <input
            type="text"
            value={data.name}
            onChange={(e) => onChange({ ...data, name: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
            placeholder="my-application"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Repository</label>
          <input
            type="text"
            value={data.repository || ''}
            onChange={(e) => onChange({ ...data, repository: e.target.value || null })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all text-sm"
            placeholder="https://github.com/user/repo"
          />
        </div>
      </div>
    </div>
  )
}

