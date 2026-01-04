import { useAuth } from '@/contexts/AuthContext';
import { useDarkMode } from '@/hooks/useDarkMode';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const { isDark, toggle } = useDarkMode();

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">Settings</h1>
          <p className="text-muted-foreground">
            Manage your account and application preferences
          </p>
        </header>

        <div className="space-y-6">
          {/* Account Information */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              Account Information
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2">
                <span className="text-muted-foreground">Email:</span>
                <span className="font-medium text-foreground">{user?.email}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-muted-foreground">User ID:</span>
                <span className="font-mono text-sm text-foreground">{user?.id}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-muted-foreground">Account Status:</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                  Active
                </span>
              </div>
            </div>
          </div>

          {/* Appearance */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              Appearance
            </h2>
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-foreground">Theme</p>
                <p className="text-sm text-muted-foreground">
                  Choose your preferred color scheme
                </p>
              </div>
              <button
                onClick={toggle}
                className="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white font-medium transition-colors"
              >
                {isDark ? 'Switch to Light' : 'Switch to Dark'}
              </button>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="bg-card border border-destructive rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-destructive mb-4">
              Danger Zone
            </h2>
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-foreground">Logout</p>
                <p className="text-sm text-muted-foreground">
                  Sign out of your account
                </p>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 rounded-lg bg-destructive hover:bg-destructive/90 text-destructive-foreground font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
