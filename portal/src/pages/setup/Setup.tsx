import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Settings, Mail, Lock, User, Check, Loader2, AlertCircle, Rocket } from 'lucide-react'
import axios from 'axios'
import { API_BASE_URL } from '../../config/api'
import { useAuth } from '../../contexts/AuthContext'

interface SetupStatus {
  initialized: boolean
  message: string
}

export default function Setup() {
  const navigate = useNavigate()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Form fields
  const [adminEmail, setAdminEmail] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [adminName, setAdminName] = useState('')

  // Field errors
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const checkSetupStatus = useCallback(async () => {
    try {
      const response = await axios.get<SetupStatus>(`${API_BASE_URL}/setup/status`)
      if (response.data.initialized) {
        // Already initialized, redirect based on auth status
        // If authenticated, go to home; otherwise go to login
        if (!authLoading) {
          navigate(isAuthenticated ? '/' : '/login')
        }
      }
    } catch (err) {
      console.error('Failed to check setup status:', err)
    } finally {
      setLoading(false)
    }
  }, [navigate, isAuthenticated, authLoading])

  useEffect(() => {
    // Wait for auth loading to complete before checking setup status
    if (!authLoading) {
      checkSetupStatus()
    }
  }, [checkSetupStatus, authLoading])

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!adminEmail) {
      errors.adminEmail = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(adminEmail)) {
      errors.adminEmail = 'Invalid email format'
    }

    if (!adminPassword) {
      errors.adminPassword = 'Password is required'
    } else if (adminPassword.length < 6) {
      errors.adminPassword = 'Password must be at least 6 characters'
    }

    if (adminPassword !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!validateForm()) {
      return
    }

    setSubmitting(true)

    try {
      await axios.post(`${API_BASE_URL}/setup/initialize`, {
        admin_email: adminEmail,
        admin_password: adminPassword,
        admin_name: adminName || 'Administrator',
      })

      setSuccess(true)

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to initialize system')
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-subtle">
        <div className="flex items-center gap-3 text-neutral-600">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Checking system status...</span>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-subtle px-4">
        <div className="w-full max-w-md text-center">
          <div className="glass-effect-strong rounded-2xl p-8 shadow-soft-lg">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-neutral-800 mb-2">Setup Complete!</h2>
            <p className="text-neutral-600 mb-4">
              Your Tron instance has been configured successfully.
            </p>
            <p className="text-sm text-neutral-500">
              Redirecting to login...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-subtle px-4 py-8">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-primary rounded-xl opacity-20 blur-md"></div>
              <div className="relative p-3 bg-gradient-primary rounded-xl shadow-soft">
                <Rocket className="w-8 h-8 text-white" />
              </div>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gradient mb-2">Welcome to Tron</h1>
          <p className="text-neutral-600">Let's set up your platform in just a few steps</p>
        </div>

        {/* Setup Form */}
        <div className="glass-effect-strong rounded-2xl p-8 shadow-soft-lg">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-neutral-200">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Settings className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-neutral-800">Initial Setup</h2>
              <p className="text-sm text-neutral-500">Create your admin account</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-error/10 border border-error/20 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" />
                <p className="text-error text-sm">{error}</p>
              </div>
            )}

            {/* Admin Email */}
            <div>
              <label htmlFor="adminEmail" className="block text-sm font-medium text-neutral-700 mb-2">
                Admin Email <span className="text-error">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-neutral-400" />
                <input
                  id="adminEmail"
                  type="email"
                  value={adminEmail}
                  onChange={(e) => {
                    setAdminEmail(e.target.value)
                    if (fieldErrors.adminEmail) setFieldErrors({ ...fieldErrors, adminEmail: '' })
                  }}
                  className={`input pl-10 w-full ${fieldErrors.adminEmail ? 'border-red-500' : ''}`}
                  placeholder="admin@company.com"
                  autoComplete="email"
                />
              </div>
              {fieldErrors.adminEmail && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.adminEmail}</p>
              )}
            </div>

            {/* Admin Name */}
            <div>
              <label htmlFor="adminName" className="block text-sm font-medium text-neutral-700 mb-2">
                Your Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-neutral-400" />
                <input
                  id="adminName"
                  type="text"
                  value={adminName}
                  onChange={(e) => setAdminName(e.target.value)}
                  className="input pl-10 w-full"
                  placeholder="John Doe"
                  autoComplete="name"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="adminPassword" className="block text-sm font-medium text-neutral-700 mb-2">
                Password <span className="text-error">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-neutral-400" />
                <input
                  id="adminPassword"
                  type="password"
                  value={adminPassword}
                  onChange={(e) => {
                    setAdminPassword(e.target.value)
                    if (fieldErrors.adminPassword) setFieldErrors({ ...fieldErrors, adminPassword: '' })
                  }}
                  className={`input pl-10 w-full ${fieldErrors.adminPassword ? 'border-red-500' : ''}`}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
              </div>
              {fieldErrors.adminPassword && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.adminPassword}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-neutral-700 mb-2">
                Confirm Password <span className="text-error">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-neutral-400" />
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value)
                    if (fieldErrors.confirmPassword) setFieldErrors({ ...fieldErrors, confirmPassword: '' })
                  }}
                  className={`input pl-10 w-full ${fieldErrors.confirmPassword ? 'border-red-500' : ''}`}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
              </div>
              {fieldErrors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-6"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Setting up...</span>
                </>
              ) : (
                <>
                  <Rocket className="w-5 h-5" />
                  <span>Complete Setup</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-neutral-500">
          <p>© {new Date().getFullYear()} Tron Platform. All rights reserved.</p>
        </div>
      </div>
    </div>
  )
}
