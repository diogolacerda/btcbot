// =============================================================================
// Data Types
// =============================================================================

export interface Account {
  id: string
  exchange: string
  mode: 'demo' | 'live'
  apiKey: string
  apiSecretMasked: string
  connectionStatus: 'connected' | 'disconnected' | 'testing'
  isActive: boolean
  createdAt: string
  lastTestedAt: string
}

export interface SystemConfig {
  /** Maximum age in hours for restoring bot state from database */
  restoreMaxAge: number
  /** Whether to load trade history automatically when bot starts */
  loadHistoryOnStart: boolean
  /** Maximum number of historical trades to load */
  historyLimit: number
}

export interface SystemInfo {
  versions: {
    btcbot: string
    backend: string
    database: string
  }
  uptime: {
    runningTime: string
    lastRestartAt: string
  }
}

// =============================================================================
// Component Props
// =============================================================================

export interface SettingsProps {
  /** List of BingX accounts configured for trading */
  accounts: Account[]
  /** Bot state configuration settings */
  systemConfig: SystemConfig
  /** Read-only system version and uptime information */
  systemInfo: SystemInfo
  /** Called when user wants to add a new BingX account */
  onAddAccount?: (account: Omit<Account, 'id' | 'createdAt' | 'lastTestedAt' | 'isActive' | 'connectionStatus'>) => void
  /** Called when user wants to test connection for an account */
  onTestConnection?: (accountId: string) => void
  /** Called when user wants to edit account credentials */
  onEditAccount?: (accountId: string, updates: Partial<Account>) => void
  /** Called when user wants to set an account as active */
  onSetActiveAccount?: (accountId: string) => void
  /** Called when user wants to remove an account */
  onRemoveAccount?: (accountId: string) => void
  /** Called when user updates system configuration */
  onUpdateSystemConfig?: (config: SystemConfig) => void
}
