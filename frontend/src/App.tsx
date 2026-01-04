import { useDarkMode } from './hooks/useDarkMode'

function App() {
  const { isDark, toggle } = useDarkMode()

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="max-w-2xl w-full space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-primary-600 dark:text-primary-400">
            BTC Grid Bot
          </h1>
          <p className="text-lg text-muted-foreground">
            Design System Configuration Test
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Dark Mode</h2>
              <p className="text-sm text-muted-foreground">
                Currently: {isDark ? 'Dark' : 'Light'} Mode
              </p>
            </div>
            <button
              onClick={toggle}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-primary-foreground rounded-md transition-colors font-medium"
            >
              Toggle Mode
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="font-semibold">Primary Colors</h3>
              <div className="flex gap-2">
                <div className="w-12 h-12 rounded bg-primary-500" />
                <div className="w-12 h-12 rounded bg-primary-600" />
                <div className="w-12 h-12 rounded bg-primary-700" />
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold">Secondary Colors</h3>
              <div className="flex gap-2">
                <div className="w-12 h-12 rounded bg-secondary-500" />
                <div className="w-12 h-12 rounded bg-secondary-600" />
                <div className="w-12 h-12 rounded bg-secondary-700" />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold">Typography</h3>
            <p className="font-sans">Font Sans: Inter - The quick brown fox jumps</p>
            <p className="font-mono">Font Mono: JetBrains Mono - 0123456789</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
