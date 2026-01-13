# Milestone 1: Foundation

> **Provide alongside:** `product-overview.md`
> **Prerequisites:** None

---

## About These Instructions

**What you're receiving:**
- Finished UI designs (React components with full styling)
- Data model definitions (TypeScript types and sample data)
- UI/UX specifications (user flows, requirements, screenshots)
- Design system tokens (colors, typography, spacing)
- Test-writing instructions for each section (for TDD approach)

**What you need to build:**
- Backend API endpoints and database schema
- Authentication and authorization
- Data fetching and state management
- Business logic and validation
- Integration of the provided UI components with real data

**Important guidelines:**
- **DO NOT** redesign or restyle the provided components — use them as-is
- **DO** wire up the callback props to your routing and API calls
- **DO** replace sample data with real data from your backend
- **DO** implement proper error handling and loading states
- **DO** implement empty states when no records exist (first-time users, after deletions)
- **DO** use test-driven development — write tests first using `tests.md` instructions
- The components are props-based and ready to integrate — focus on the backend and data layer

---

## Goal

Set up the foundational elements: design tokens, data model types, routing structure, and application shell.

## What to Implement

### 1. Design Tokens

Configure your styling system with these tokens:

- See `product-plan/design-system/tokens.css` for CSS custom properties
- See `product-plan/design-system/tailwind-colors.md` for Tailwind configuration
- See `product-plan/design-system/fonts.md` for Google Fonts setup

**Key Colors:**
- Primary: `emerald` (buttons, links, active states)
- Secondary: `amber` (tags, highlights)
- Neutral: `slate` (backgrounds, text, borders)

**Typography:**
- Heading & Body: Inter
- Code/Mono: JetBrains Mono

Import Google Fonts in your HTML `<head>`:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### 2. Data Model Types

Create TypeScript interfaces for your core entities:

- See `product-plan/data-model/types.ts` for interface definitions
- See `product-plan/data-model/README.md` for entity relationships

**Core Entities:**
- **User** — Application user
- **Account** — BingX exchange account connection
- **Strategy** — Trading strategy configuration
- **Trade** — Completed trade record
- **Order** — Active exchange order
- **Position** — Open exchange position

Copy the types from `product-plan/data-model/types.ts` to your project and extend as needed for your backend.

### 3. Routing Structure

Create placeholder routes for each section:

- `/` or `/dashboard` — Dashboard (default/home)
- `/trade-history` — Trade History
- `/strategy` — Strategy Configuration
- `/settings` — Settings

For now, these can render simple placeholder pages. You'll replace them with real section implementations in later milestones.

### 4. Application Shell

Copy the shell components from `product-plan/shell/components/` to your project:

- `AppShell.tsx` — Main layout wrapper
- `MainNav.tsx` — Navigation component
- `UserMenu.tsx` — User menu with avatar

**Wire Up Navigation:**

Connect navigation to your routing:

```typescript
const navigationItems = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Trade History', href: '/trade-history', icon: History },
  { label: 'Strategy', href: '/strategy', icon: Target },
  { label: 'Settings', href: '/settings', icon: Settings },
]

// Mark current route as active
navigationItems.forEach(item => {
  item.isActive = currentPath === item.href
})
```

**User Menu:**

The user menu expects:
- User name (required)
- Avatar URL (optional — shows initials if not provided)
- Logout callback

Example integration:
```typescript
const user = {
  name: currentUser.name,
  avatarUrl: currentUser.avatarUrl, // optional
}

function handleLogout() {
  // Clear session, redirect to login
}

<AppShell
  navigationItems={navigationItems}
  user={user}
  onNavigate={(href) => router.push(href)}
  onLogout={handleLogout}
>
  {children}
</AppShell>
```

## Files to Reference

- `product-plan/design-system/` — Design tokens
- `product-plan/data-model/` — Type definitions
- `product-plan/shell/README.md` — Shell design intent
- `product-plan/shell/components/` — Shell React components

## Done When

- [ ] Design tokens are configured (Tailwind colors, fonts loaded)
- [ ] Data model types are defined in your project
- [ ] Routes exist for all sections (can be placeholder pages)
- [ ] Shell renders with navigation
- [ ] Navigation links to correct routes
- [ ] User menu shows user info
- [ ] Logout works
- [ ] Responsive on mobile (sidebar collapses to hamburger menu)
- [ ] Light and dark mode both work
