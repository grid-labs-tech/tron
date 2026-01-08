import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../services/api'
import { User, Save, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { Breadcrumbs } from '../components/Breadcrumbs'

export default function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [email, setEmail] = useState(user?.email || '')
  const [fullName, setFullName] = useState(user?.full_name || '')

  // Atualizar campos quando o usuário mudar
  useEffect(() => {
    if (user) {
      setEmail(user.email || '')
      setFullName(user.full_name || '')
    }
  }, [user])
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const updateProfileMutation = useMutation({
    mutationFn: async (data: { email?: string; full_name?: string; password?: string; current_password?: string }) => {
      return await authApi.updateProfile(data)
    },
    onSuccess: (updatedUser) => {
      setSuccess('Profile updated successfully!')
      setError(null)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')

      // Atualizar cache do usuário
      queryClient.setQueryData(['user'], updatedUser)

      // Se mudou a senha ou email, fazer logout para forçar novo login
      if (newPassword || (email && email !== user?.email)) {
        setTimeout(() => {
          logout()
          navigate('/login')
        }, 2000)
      }
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Error updating profile')
      setSuccess(null)
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    // Validação de email
    if (email && email !== user?.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email)) {
        setError('Invalid email')
        return
      }
    }

    // Validações de senha
    if (newPassword && newPassword.length < 6) {
      setError('New password must be at least 6 characters')
      return
    }

    if (newPassword && newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (newPassword && !currentPassword) {
      setError('Current password is required to change password')
      return
    }

    // Preparar dados para atualização
    const updateData: { email?: string; full_name?: string; password?: string; current_password?: string } = {}

    if (email && email !== user?.email) {
      updateData.email = email
    }

    if (fullName !== user?.full_name) {
      updateData.full_name = fullName || null
    }

    if (newPassword) {
      updateData.password = newPassword
      updateData.current_password = currentPassword
    }

    // Só atualizar se houver mudanças
    if (Object.keys(updateData).length === 0) {
      setError('No changes were made')
      return
    }

    updateProfileMutation.mutate(updateData)
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Profile', path: '/profile' },
        ]}
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">My Profile</h1>
          <p className="text-neutral-600 mt-1">Manage your personal information and password</p>
        </div>
      </div>

      <div className="glass-effect-strong rounded-2xl p-8 shadow-soft-lg">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-error/10 border border-error/20 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" />
              <p className="text-error text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
              <p className="text-success text-sm">{success}</p>
            </div>
          )}

          {/* Informações do Usuário */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-neutral-800 flex items-center gap-2">
              <User className="w-5 h-5" />
              Personal Information
            </h2>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input w-full"
                placeholder="your@email.com"
                required
              />
            </div>

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-neutral-700 mb-2">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="input w-full"
                placeholder="Your full name"
              />
            </div>
          </div>

          {/* Alteração de Senha */}
          <div className="space-y-4 pt-6 border-t border-neutral-200">
            <h2 className="text-xl font-semibold text-neutral-800 flex items-center gap-2">
              <Save className="w-5 h-5" />
              Change Password
            </h2>
            <p className="text-sm text-neutral-600">
              Leave blank if you don't want to change the password
            </p>

            <div>
              <label htmlFor="currentPassword" className="block text-sm font-medium text-neutral-700 mb-2">
                Current Password
              </label>
              <div className="relative">
                <input
                  id="currentPassword"
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="input w-full pr-10"
                  placeholder="Enter your current password"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
                >
                  {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-neutral-700 mb-2">
                New Password
              </label>
              <div className="relative">
                <input
                  id="newPassword"
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input w-full pr-10"
                  placeholder="Enter new password (minimum 6 characters)"
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
                >
                  {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-neutral-700 mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input w-full pr-10"
                  placeholder="Confirm new password"
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          {/* Botões */}
          <div className="flex items-center justify-end gap-4 pt-6 border-t border-neutral-200">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateProfileMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              {updateProfileMutation.isPending ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

