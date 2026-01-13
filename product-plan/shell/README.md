# Application Shell

## Overview

The Btcbot application shell provides a professional dashboard layout with persistent sidebar navigation. The design prioritizes quick access to all sections while keeping the focus on real-time trading data and analytics.

## Navigation Structure

- Dashboard → Dashboard section (real-time monitoring)
- Trade History → Trade History section (performance tracking)
- Strategy → Strategy section (configuration and controls)
- Settings → Settings section (general configuration)

## User Menu

Located in the top right corner of the content area, the user menu displays:
- User avatar (or initials if no avatar)
- User name
- Dropdown menu with logout option

## Layout Pattern

**Sidebar Navigation:** Fixed left sidebar (240px wide on desktop) with navigation items and branding. Content area fills the remaining space on the right.

The sidebar uses a clean, minimal design with:
- Btcbot logo/name at the top
- Navigation items with icons
- Emerald accent color for active items
- Slate background for the sidebar

## Responsive Behavior

- **Desktop:** Fixed sidebar on left (240px), content area fills remaining space with user menu in top right
- **Tablet:** Same as desktop layout
- **Mobile:** Sidebar collapses to hamburger menu icon in top left, slides in from left when opened, overlay dims content area, maximizes screen space for charts and data tables

## Design Notes

- Uses emerald (primary) for active navigation items and key accents
- Uses amber (secondary) for hover states and subtle highlights
- Uses slate (neutral) for sidebar background, borders, and muted text
- Supports light and dark mode throughout
- Inter font for all text
- Icons from lucide-react (LayoutDashboard, History, Target, Settings)
- Mobile-first responsive design

## Components Provided

- `AppShell.tsx` — Main layout wrapper with sidebar, header, and content area
- `MainNav.tsx` — Sidebar navigation component with logo and nav items
- `UserMenu.tsx` — User menu dropdown with avatar and logout
- `index.ts` — Component exports

## Integration

```typescript
import { AppShell } from './shell/components'
import { LayoutDashboard, History, Target, Settings } from 'lucide-react'

function App() {
  const navigationItems = [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, isActive: true },
    { label: 'Trade History', href: '/trade-history', icon: History },
    { label: 'Strategy', href: '/strategy', icon: Target },
    { label: 'Settings', href: '/settings', icon: Settings },
  ]

  const user = {
    name: 'Demo User',
    avatarUrl: '/path/to/avatar.jpg', // optional
  }

  return (
    <AppShell
      navigationItems={navigationItems}
      user={user}
      onNavigate={(href) => {
        // Handle navigation - e.g., router.push(href)
      }}
      onLogout={() => {
        // Handle logout
      }}
    >
      {/* Your page content */}
    </AppShell>
  )
}
```

## Props

### AppShellProps

| Prop | Type | Description |
|------|------|-------------|
| `children` | `React.ReactNode` | Page content to render |
| `navigationItems` | `NavigationItem[]` | Array of nav items with label, href, icon, isActive |
| `user` | `User` | User object with name and optional avatarUrl |
| `onNavigate` | `(href: string) => void` | Called when nav item is clicked |
| `onLogout` | `() => void` | Called when logout is clicked |
