import { useState } from 'react'
import { Plus, CheckCircle, XCircle } from 'lucide-react'
import { AccountCard } from './AccountCard'
import { AddAccountModal } from './AddAccountModal'
import { EditAccountModal } from './EditAccountModal'
import { ConfirmDialog } from './ConfirmDialog'
import type { SettingsProps, Account, SystemConfig } from '@/../product/sections/settings/types'

type Tab = 'accounts' | 'system' | 'about'
type ToastType = 'success' | 'error' | null

export function Settings({
  accounts,
  systemConfig,
  systemInfo,
  onAddAccount,
  onTestConnection,
  onEditAccount,
  onSetActiveAccount,
  onRemoveAccount,
  onUpdateSystemConfig,
}: SettingsProps) {
  const [activeTab, setActiveTab] = useState<Tab>('accounts')
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [confirmDialog, setConfirmDialog] = useState<{
    type: 'setActive' | 'remove' | null
    accountId: string | null
  }>({ type: null, accountId: null })
  const [testingAccountId, setTestingAccountId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ type: ToastType; message: string }>({
    type: null,
    message: '',
  })
  const [config, setConfig] = useState<SystemConfig>(systemConfig)

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast({ type: null, message: '' }), 3000)
  }

  const handleTestConnection = async (accountId: string) => {
    setTestingAccountId(accountId)
    onTestConnection?.(accountId)

    // Simulate async test
    setTimeout(() => {
      setTestingAccountId(null)
      showToast('success', 'Connection test successful')
    }, 1500)
  }

  const handleSetActive = () => {
    if (confirmDialog.accountId) {
      onSetActiveAccount?.(confirmDialog.accountId)
      showToast('success', 'Active account changed successfully')
      setConfirmDialog({ type: null, accountId: null })
    }
  }

  const handleRemove = () => {
    if (confirmDialog.accountId) {
      onRemoveAccount?.(confirmDialog.accountId)
      showToast('success', 'Account removed successfully')
      setConfirmDialog({ type: null, accountId: null })
    }
  }

  const handleSaveConfig = () => {
    onUpdateSystemConfig?.(config)
    showToast('success', 'System configuration saved successfully')
  }

  const formatUptime = (uptime: string) => {
    return uptime
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Toast Notification */}
      {toast.type && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right">
          <div
            className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg ${
              toast.type === 'success'
                ? 'bg-emerald-600 text-white'
                : 'bg-red-600 text-white'
            }`}
          >
            {toast.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <XCircle className="w-5 h-5" />
            )}
            <span className="font-medium">{toast.message}</span>
          </div>
        </div>
      )}

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Settings</h1>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <div className="flex gap-8">
          <button
            onClick={() => setActiveTab('accounts')}
            className={`pb-3 border-b-2 transition-colors font-medium ${
              activeTab === 'accounts'
                ? 'border-emerald-600 dark:border-emerald-400 text-emerald-600 dark:text-emerald-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
            }`}
          >
            Accounts
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`pb-3 border-b-2 transition-colors font-medium ${
              activeTab === 'system'
                ? 'border-emerald-600 dark:border-emerald-400 text-emerald-600 dark:text-emerald-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
            }`}
          >
            System
          </button>
          <button
            onClick={() => setActiveTab('about')}
            className={`pb-3 border-b-2 transition-colors font-medium ${
              activeTab === 'about'
                ? 'border-emerald-600 dark:border-emerald-400 text-emerald-600 dark:text-emerald-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
            }`}
          >
            About
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'accounts' && (
        <div className="space-y-4">
          {/* Add Account Button */}
          <div className="flex justify-end">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
            >
              <Plus className="w-4 h-4" />
              Add Account
            </button>
          </div>

          {/* Accounts List */}
          <div className="grid gap-4">
            {accounts.map((account) => (
              <AccountCard
                key={account.id}
                account={account}
                onTestConnection={handleTestConnection}
                onEdit={(id) => setEditingAccount(accounts.find((a) => a.id === id) || null)}
                onSetActive={(id) => setConfirmDialog({ type: 'setActive', accountId: id })}
                onRemove={(id) => setConfirmDialog({ type: 'remove', accountId: id })}
                isTestingConnection={testingAccountId === account.id}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'system' && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Bot State Configuration
          </h2>

          <div className="space-y-4">
            {/* Restore Max Age */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Restore Max Age (hours)
              </label>
              <input
                type="number"
                value={config.restoreMaxAge}
                onChange={(e) =>
                  setConfig({ ...config, restoreMaxAge: parseInt(e.target.value) })
                }
                min="1"
                max="168"
                className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Maximum age of saved state to restore on bot restart (1-168 hours)
              </p>
            </div>

            {/* Load History on Start */}
            <div>
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                    Load History on Start
                  </label>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Automatically load trade history when bot starts
                  </p>
                </div>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={config.loadHistoryOnStart}
                    onChange={(e) =>
                      setConfig({ ...config, loadHistoryOnStart: e.target.checked })
                    }
                    className="sr-only peer"
                  />
                  <div
                    onClick={() =>
                      setConfig({ ...config, loadHistoryOnStart: !config.loadHistoryOnStart })
                    }
                    className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-emerald-500 dark:peer-focus:ring-emerald-400 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600 cursor-pointer"
                  ></div>
                </div>
              </div>
            </div>

            {/* History Limit */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                History Limit
              </label>
              <input
                type="number"
                value={config.historyLimit}
                onChange={(e) => setConfig({ ...config, historyLimit: parseInt(e.target.value) })}
                min="10"
                max="1000"
                className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Maximum number of historical trades to load (10-1000)
              </p>
            </div>

            {/* Save Button */}
            <div className="pt-4">
              <button
                onClick={handleSaveConfig}
                className="w-full px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
              >
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'about' && (
        <div className="space-y-6">
          {/* Version Info */}
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
              Version Information
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Btcbot</span>
                <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                  v{systemInfo.versions.btcbot}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Backend</span>
                <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                  {systemInfo.versions.backend}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Database</span>
                <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                  {systemInfo.versions.database}
                </span>
              </div>
            </div>
          </div>

          {/* Uptime */}
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
              Uptime
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Running Time</span>
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  {formatUptime(systemInfo.uptime.runningTime)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Last Restart</span>
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  {formatDateTime(systemInfo.uptime.lastRestartAt)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <AddAccountModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={(account) => {
          onAddAccount?.(account)
          showToast('success', 'Account added successfully')
        }}
      />

      <EditAccountModal
        isOpen={!!editingAccount}
        account={editingAccount}
        onClose={() => setEditingAccount(null)}
        onEdit={(id, updates) => {
          onEditAccount?.(id, updates)
          showToast('success', 'Account credentials updated successfully')
          setEditingAccount(null)
        }}
      />

      <ConfirmDialog
        isOpen={confirmDialog.type === 'setActive'}
        title="Set Active Account?"
        message="The bot will switch to this account and start trading with it. Make sure the API credentials are correct."
        confirmLabel="Set Active"
        variant="info"
        onConfirm={handleSetActive}
        onCancel={() => setConfirmDialog({ type: null, accountId: null })}
      />

      <ConfirmDialog
        isOpen={confirmDialog.type === 'remove'}
        title="Remove Account?"
        message="This will permanently delete this account configuration. This action cannot be undone."
        confirmLabel="Remove"
        variant="danger"
        onConfirm={handleRemove}
        onCancel={() => setConfirmDialog({ type: null, accountId: null })}
      />
    </div>
  )
}
