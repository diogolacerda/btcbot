import { useAuth } from '@/contexts/AuthContext';

export function TradeHistoryPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Trade History
          </h1>
          <p className="text-muted-foreground">
            View your complete trading history and performance metrics
          </p>
        </header>

        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/20 mb-4">
              <svg
                className="w-8 h-8 text-primary-600 dark:text-primary-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-foreground mb-2">
              Trade History Coming Soon
            </h2>
            <p className="text-muted-foreground max-w-md mx-auto">
              This page will display your complete trading history with detailed
              analytics, profit/loss charts, and performance metrics.
            </p>
            {user && (
              <p className="text-sm text-muted-foreground mt-4">
                Logged in as: {user.email}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
