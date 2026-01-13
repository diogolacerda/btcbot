import { useState, useEffect } from 'react'
import { X, Eye, EyeOff } from 'lucide-react'
import type { Account } from '@/../product/sections/settings/types'

interface EditAccountModalProps {
  isOpen: boolean
  account: Account | null
  onClose: () => void
  onEdit?: (accountId: string, updates: Partial<Account>) => void
}

export function EditAccountModal({ isOpen, account, onClose, onEdit }: EditAccountModalProps) {
  const [formData, setFormData] = useState({
    apiKey: '',
    apiSecret: '',
  })
  const [showSecret, setShowSecret] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (account) {
      setFormData({
        apiKey: account.apiKey.replace(/••+/g, ''),
        apiSecret: '',
      })
    }
  }, [account])

  if (!isOpen || !account) return null

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.apiKey.trim()) {
      newErrors.apiKey = 'API Key is required'
    } else if (formData.apiKey.length < 20) {
      newErrors.apiKey = 'API Key must be at least 20 characters'
    }

    if (formData.apiSecret && formData.apiSecret.length < 20) {
      newErrors.apiSecret = 'API Secret must be at least 20 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    const updates: Partial<Account> = {
      apiKey: formData.apiKey,
    }

    if (formData.apiSecret) {
      updates.apiSecretMasked = '••••••••••••••••'
    }

    onEdit?.(account.id, updates)

    setFormData({ apiKey: '', apiSecret: '' })
    setErrors({})
    onClose()
  }

  const handleClose = () => {
    setFormData({ apiKey: '', apiSecret: '' })
    setErrors({})
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Edit Account
          </h2>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Account Info */}
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              <span className="font-medium">Exchange:</span> {account.exchange}
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              <span className="font-medium">Mode:</span>{' '}
              <span className="capitalize">{account.mode}</span>
            </p>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              API Key
            </label>
            <input
              type="text"
              value={formData.apiKey}
              onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
              placeholder="Enter new API key"
              className={`w-full px-4 py-2 bg-white dark:bg-slate-900 border rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 ${
                errors.apiKey
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-slate-200 dark:border-slate-700 focus:ring-emerald-500'
              }`}
            />
            {errors.apiKey && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.apiKey}</p>
            )}
          </div>

          {/* API Secret */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              API Secret
            </label>
            <div className="relative">
              <input
                type={showSecret ? 'text' : 'password'}
                value={formData.apiSecret}
                onChange={(e) => setFormData({ ...formData, apiSecret: e.target.value })}
                placeholder="Enter new API secret (optional)"
                className={`w-full px-4 py-2 pr-10 bg-white dark:bg-slate-900 border rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 ${
                  errors.apiSecret
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-200 dark:border-slate-700 focus:ring-emerald-500'
                }`}
              />
              <button
                type="button"
                onClick={() => setShowSecret(!showSecret)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.apiSecret && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.apiSecret}</p>
            )}
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Leave blank to keep current secret
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
