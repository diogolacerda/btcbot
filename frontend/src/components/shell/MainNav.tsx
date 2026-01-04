import { LayoutDashboard, History, Target, Settings } from 'lucide-react'
import type { NavigationItem } from './AppShell'

export interface MainNavProps {
  items: NavigationItem[]
  onNavigate?: (href: string) => void
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Dashboard: LayoutDashboard,
  'Trade History': History,
  Strategy: Target,
  Settings: Settings,
}

export function MainNav({ items, onNavigate }: MainNavProps) {
  const handleClick = (href: string, e: React.MouseEvent) => {
    e.preventDefault()
    onNavigate?.(href)
  }

  return (
    <nav className="flex flex-col h-full">
      {/* Logo/Brand */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-800">
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
          Btcbot
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Grid Trading Bot
        </p>
      </div>

      {/* Navigation items */}
      <div className="flex-1 p-3 space-y-1">
        {items.map((item) => {
          const Icon = item.icon || iconMap[item.label]
          const isActive = item.isActive

          return (
            <a
              key={item.href}
              href={item.href}
              onClick={(e) => handleClick(item.href, e)}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-lg
                transition-colors duration-150
                ${
                  isActive
                    ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-medium'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800'
                }
              `}
            >
              {Icon && (
                <Icon
                  className={`w-5 h-5 ${
                    isActive
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-slate-500 dark:text-slate-400'
                  }`}
                />
              )}
              <span className="text-sm">{item.label}</span>
            </a>
          )
        })}
      </div>
    </nav>
  )
}
