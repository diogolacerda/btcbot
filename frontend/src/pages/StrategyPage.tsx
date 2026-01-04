import { useAuth } from '@/contexts/AuthContext';

export function StrategyPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Strategy Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure your grid trading strategy and risk parameters
          </p>
        </header>

        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-secondary-100 dark:bg-secondary-900/20 mb-4">
              <svg
                className="w-8 h-8 text-secondary-600 dark:text-secondary-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-foreground mb-2">
              Strategy Settings Coming Soon
            </h2>
            <p className="text-muted-foreground max-w-md mx-auto">
              Configure grid levels, MACD parameters, take profit percentages,
              and other strategy settings for your trading bot.
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
