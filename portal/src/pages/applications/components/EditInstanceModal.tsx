import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import type { Instance } from '../../../features/instances'
import type { Application } from '../../../features/applications'

interface EditInstanceModalProps {
  instance: Instance
  application: Application | undefined
  isOpen: boolean
  onClose: () => void
  onUpdate: (data: { image: string; version: string; enabled: boolean }) => void
  isUpdating: boolean
}

export const EditInstanceModal = ({
  instance,
  application,
  isOpen,
  onClose,
  onUpdate,
  isUpdating,
}: EditInstanceModalProps) => {
  const [formData, setFormData] = useState({
    image: instance.image,
    version: instance.version,
    enabled: instance.enabled,
  })

  useEffect(() => {
    if (isOpen && instance) {
      setFormData({
        image: instance.image,
        version: instance.version,
        enabled: instance.enabled,
      })
    }
  }, [isOpen, instance])

  if (!isOpen) return null

  const handleSubmit = () => {
    if (!formData.image || !formData.version) {
      return
    }
    onUpdate(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-soft-lg max-w-2xl w-full border border-slate-200/60 animate-zoom-in">
        <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Edit Instance</h2>
            <p className="text-xs text-slate-500 mt-1">
              Application: {application?.name || 'N/A'} | Environment: {instance.environment.name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Image <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.image}
              onChange={(e) => setFormData({ ...formData, image: e.target.value })}
              placeholder="e.g., myapp"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Version <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.version}
              onChange={(e) => setFormData({ ...formData, version: e.target.value })}
              placeholder="e.g., 1.0.0"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
            />
          </div>
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-slate-700">Enabled</span>
            </label>
            <p className="text-xs text-slate-500 mt-1 ml-6">
              When enabled, the instance will be active and can receive traffic.
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 px-5 pb-5">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isUpdating || !formData.image || !formData.version}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-soft text-sm font-medium disabled:opacity-50"
          >
            {isUpdating ? 'Updating...' : 'Update Instance'}
          </button>
        </div>
      </div>
    </div>
  )
}
