import { Eye, EyeOff, X, Lock, Loader2 } from 'lucide-react'
import { useState, useCallback, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from '../../../config/api'

interface Secret {
  key: string
  value: string
}

interface SecretsInputProps {
  secrets: Secret[]
  onChange: (secrets: Secret[]) => void
  isAdmin?: boolean
  componentUuid?: string
  componentType?: 'webapp' | 'worker' | 'cron'
}

export function SecretsInput({ secrets, onChange, isAdmin = false, componentUuid, componentType }: SecretsInputProps) {
  const [showValues, setShowValues] = useState<Record<number, boolean>>({})
  const [decryptedSecrets, setDecryptedSecrets] = useState<Secret[]>([])
  const [loadingSecrets, setLoadingSecrets] = useState<Record<number, boolean>>({})
  const [hasFetchedSecrets, setHasFetchedSecrets] = useState(false)

  // Security: Clear decrypted secrets from memory when component unmounts
  // or when componentUuid changes (different component selected)
  useEffect(() => {
    return () => {
      // Clear sensitive data from state on unmount
      setDecryptedSecrets([])
      setShowValues({})
      setHasFetchedSecrets(false)
    }
  }, [])

  // Reset state when component changes
  useEffect(() => {
    setDecryptedSecrets([])
    setShowValues({})
    setHasFetchedSecrets(false)
  }, [componentUuid])

  const addSecret = () => {
    onChange([...secrets, { key: '', value: '' }])
  }

  const updateSecret = (index: number, field: 'key' | 'value', value: string) => {
    const updated = secrets.map((secret, i) =>
      i === index ? { ...secret, [field]: value } : secret
    )
    onChange(updated)
  }

  const removeSecret = (index: number) => {
    onChange(secrets.filter((_, i) => i !== index))
    // Clean up showValues state
    const newShowValues = { ...showValues }
    delete newShowValues[index]
    setShowValues(newShowValues)
  }

  const fetchDecryptedSecrets = useCallback(async () => {
    if (!componentUuid || !componentType) {
      return null
    }
    
    try {
      const token = localStorage.getItem('access_token')
      const url = `${API_BASE_URL}/application_components/${componentType}/${componentUuid}/secrets`
      
      const response = await axios.get<{ secrets: Secret[] }>(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      })
      return response.data.secrets
    } catch (error) {
      console.error('Failed to fetch decrypted secrets', error)
    }
    return null
  }, [componentUuid, componentType])

  const toggleShowValue = async (index: number) => {
    const secret = secrets[index]
    
    // If already showing, just hide
    if (showValues[index]) {
      setShowValues(prev => ({ ...prev, [index]: false }))
      return
    }
    
    // For masked values, admin needs to fetch decrypted value
    if (isValueMasked(secret.value) && isAdmin) {
      // Fetch if not already fetched
      if (!hasFetchedSecrets) {
        setLoadingSecrets(prev => ({ ...prev, [index]: true }))
        const decrypted = await fetchDecryptedSecrets()
        setLoadingSecrets(prev => ({ ...prev, [index]: false }))
        
        if (decrypted) {
          setDecryptedSecrets(decrypted)
          setHasFetchedSecrets(true)
        }
      }
      
      setShowValues(prev => ({ ...prev, [index]: true }))
      return
    }
    
    // For non-masked values, just toggle
    if (!isValueMasked(secret.value)) {
      setShowValues(prev => ({ ...prev, [index]: !prev[index] }))
    }
  }

  const isValueMasked = (value: string) => value === '********'

  // Check if toggle should be disabled (masked value and not admin)
  const isToggleDisabled = (value: string) => isValueMasked(value) && !isAdmin

  // Get display value for a secret (decrypted if available and showing)
  const getDisplayValue = (secret: Secret, index: number): string => {
    if (showValues[index] && isValueMasked(secret.value)) {
      // Find decrypted value by key
      const decrypted = decryptedSecrets.find(s => s.key === secret.key)
      if (decrypted) {
        return decrypted.value
      }
    }
    return secret.value
  }

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-slate-50/50">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Lock size={14} className="text-slate-500" />
          <div>
            <h5 className="text-xs font-semibold text-slate-700">Secrets</h5>
            <p className="text-xs text-slate-500">Encrypted and stored securely</p>
          </div>
        </div>
        <button
          type="button"
          onClick={addSecret}
          className="text-xs text-blue-600 hover:text-blue-700"
        >
          + Add Secret
        </button>
      </div>
      {secrets.map((secret, secretIndex) => (
        <div key={secretIndex} className="mb-2 grid grid-cols-[1fr_1fr_auto_auto] gap-2 items-center">
          <div>
            <input
              type="text"
              value={secret.key}
              onChange={(e) => updateSecret(secretIndex, 'key', e.target.value)}
              placeholder="Secret Key"
              className="w-full px-2 py-1 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
              disabled={isValueMasked(secret.value)}
            />
          </div>
          <div className="relative">
            <input
              type={showValues[secretIndex] ? 'text' : 'password'}
              value={getDisplayValue(secret, secretIndex)}
              onChange={(e) => updateSecret(secretIndex, 'value', e.target.value)}
              placeholder={isValueMasked(secret.value) ? '(encrypted)' : 'Secret Value'}
              className="w-full px-2 py-1 pr-8 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400"
              disabled={isValueMasked(secret.value)}
              readOnly={isValueMasked(secret.value)}
            />
          </div>
          <button
            type="button"
            onClick={() => toggleShowValue(secretIndex)}
            className={`px-2 py-1 rounded text-xs ${
              isToggleDisabled(secret.value)
                ? 'text-slate-300 cursor-not-allowed'
                : 'text-slate-500 hover:bg-slate-100'
            }`}
            title={
              isToggleDisabled(secret.value)
                ? 'Only admins can view existing secrets'
                : showValues[secretIndex] ? 'Hide value' : 'Show value'
            }
            disabled={isToggleDisabled(secret.value) || loadingSecrets[secretIndex]}
          >
            {loadingSecrets[secretIndex] ? (
              <Loader2 size={14} className="animate-spin" />
            ) : showValues[secretIndex] ? (
              <EyeOff size={14} />
            ) : (
              <Eye size={14} />
            )}
          </button>
          <button
            type="button"
            onClick={() => removeSecret(secretIndex)}
            className="px-2 py-1 text-red-600 hover:bg-red-50 rounded text-xs"
            title="Remove secret"
          >
            <X size={14} />
          </button>
        </div>
      ))}
      {secrets.length === 0 && (
        <p className="text-xs text-slate-400 text-center py-2">
          No secrets configured. Click "+ Add Secret" to add one.
        </p>
      )}
    </div>
  )
}
