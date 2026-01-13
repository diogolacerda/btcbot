import { AlertCircle } from 'lucide-react'

interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  message: string
  confirmLabel: string
  cancelLabel?: string
  variant?: 'danger' | 'warning' | 'info'
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel,
  cancelLabel = 'Cancel',
  variant = 'info',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null

  const variantStyles = {
    danger: {
      icon: 'text-red-600 dark:text-red-400',
      button: 'bg-red-600 hover:bg-red-700',
    },
    warning: {
      icon: 'text-amber-600 dark:text-amber-400',
      button: 'bg-amber-600 hover:bg-amber-700',
    },
    info: {
      icon: 'text-emerald-600 dark:text-emerald-400',
      button: 'bg-emerald-600 hover:bg-emerald-700',
    },
  }

  const styles = variantStyles[variant]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex items-start gap-3 mb-4">
          <AlertCircle className={`w-6 h-6 ${styles.icon} flex-shrink-0 mt-0.5`} />
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
              {title}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">{message}</p>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors font-medium"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors font-medium ${styles.button}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
