import { useAuth } from '@/contexts/AuthContext'

export function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-primary-600 dark:text-primary-400">
              Dashboard
            </h1>
            <p className="text-muted-foreground mt-1">
              Welcome back, {user?.email}
            </p>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 border border-border hover:bg-muted rounded-md transition-colors"
          >
            Sign out
          </button>
        </div>

        {/* Content */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Account Information</h2>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-muted-foreground">Email:</span>{' '}
              <span className="font-medium">{user?.email}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Name:</span>{' '}
              <span className="font-medium">{user?.name || 'Not set'}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Status:</span>{' '}
              <span className="font-medium">
                {user?.isActive ? (
                  <span className="text-green-600 dark:text-green-400">Active</span>
                ) : (
                  <span className="text-red-600 dark:text-red-400">Inactive</span>
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Placeholder for future features */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Trading Dashboard</h2>
          <p className="text-muted-foreground">
            Trading dashboard coming soon...
          </p>
        </div>
      </div>
    </div>
  )
}
