# Milestone 5: Settings

> **Provide alongside:** `product-overview.md`
> **Prerequisites:** Milestone 1 (Foundation) complete, Milestone 2 (Dashboard) complete, Milestone 3 (Trade History) complete, Milestone 4 (Strategy) complete

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
- **DO NOT** redesign or restyle the provided components - use them as-is
- **DO** wire up the callback props to your routing and API calls
- **DO** replace sample data with real data from your backend
- **DO** implement proper error handling and loading states
- **DO** implement empty states when no records exist (first-time users, after deletions)
- **DO** use test-driven development - write tests first using `tests.md` instructions
- The components are props-based and ready to integrate - focus on the backend and data layer

---

## Goal

Implement the Settings feature - system-level configuration including exchange account management, bot state configuration, and system information.

## Overview

The Settings section provides system-level configuration management including BingX account connections, bot state configuration, and system information. Users can manage multiple exchange accounts (demo/live), configure bot behavior settings that are currently environment variables, and view version and uptime information across three organized tabs. This section enables users to safely manage their trading infrastructure.

**Key Functionality:**
- View all connected BingX accounts with status, mode (demo/live), and connection indicators
- Add new BingX accounts via modal with API key/secret and mode selection
- Test connection to validate API credentials with BingX exchange
- Edit existing account credentials securely (API key/secret masked)
- Set active account to switch which account the bot uses for trading
- Remove accounts with confirmation dialogs
- View and update bot state configuration (restore max age, load history on start toggle, history limit)
- View system version information (Btcbot, backend, database versions)
- View uptime metrics (bot running time, last restart timestamp)

## Recommended Approach: Test-Driven Development

Before implementing this section, **write tests first** based on the test specifications provided.

See `product-plan/sections/settings/tests.md` for detailed test-writing instructions including:
- Key user flows to test (success and failure paths)
- Specific UI elements, button labels, and interactions to verify
- Expected behaviors and assertions

The test instructions are framework-agnostic - adapt them to your testing setup (Jest, Vitest, Playwright, Cypress, RSpec, Minitest, PHPUnit, etc.).

**TDD Workflow:**
1. Read `tests.md` and write failing tests for the key user flows
2. Implement the feature to make tests pass
3. Refactor while keeping tests green

## What to Implement

### Components

Copy the section components from `product-plan/sections/settings/components/`:

- `Settings.tsx` - Main container with tab navigation (Accounts/System/About)
- `AccountCard.tsx` - Individual account display with mode badge, connection status, masked credentials, action buttons
- `AddAccountModal.tsx` - Form to add new BingX account (API key/secret, demo/live mode)
- `EditAccountModal.tsx` - Form to edit existing account credentials
- `ConfirmDialog.tsx` - Reusable confirmation for account removal and active account changes

### Data Layer

The components expect these data shapes (see `types.ts`):

**Account:**
- ID, exchange name ("BingX" for MVP)
- Mode: demo or live
- API key and masked API secret (for security, only last 4 chars of secret visible)
- Connection status: connected/disconnected/testing
- Active flag: indicates which account bot is currently using
- Created and last tested timestamps

**SystemConfig:**
- Restore max age (hours): how old state can be when restoring from database
- Load history on start (boolean): whether to load trade history when bot starts
- History limit (number): maximum trades to load

**SystemInfo:**
- Versions: Btcbot version, backend (Python) version, database (PostgreSQL) version
- Uptime: bot running time (human-readable), last restart timestamp

You'll need to:
- Create API endpoints to manage accounts (list, add, edit, test connection, set active, remove)
- Store account credentials securely (encrypt API secrets in database)
- Implement connection testing by calling BingX API to validate credentials
- Ensure only one account can be active at a time
- Prevent removing the active account (require user to set another as active first)
- Create API endpoints to get and update system configuration
- Store system config persistently (database or configuration file)
- Create endpoint to fetch system info (versions from build/env, uptime from runtime)
- Implement security checks: only account owner can manage their accounts

### Callbacks

Wire up these user actions:

| Callback | Description | Implementation Notes |
|----------|-------------|---------------------|
| `onAddAccount` | Called when user submits new account form (passes account data without ID or timestamps) | Validate API key/secret format. Store credentials securely (encrypt secret). Test connection optionally. Add account to database. Return new account with ID. |
| `onTestConnection` | Called when user clicks "Test Connection" to validate API credentials (passes account ID) | Fetch account credentials from database (decrypt secret). Make test API call to BingX (e.g., fetch account balance or info). Update connection status based on result. Return success/failure. |
| `onEditAccount` | Called when user saves edited account credentials (passes account ID and updated fields) | Validate new credentials. Update account in database (re-encrypt secret if changed). Optionally re-test connection. Return success/failure. |
| `onSetActiveAccount` | Called when user clicks "Set Active" to switch trading to this account (passes account ID) | Check if bot is currently running (if yes, warn or block). Set all accounts' isActive to false. Set specified account's isActive to true. Update bot to use new account credentials. Return success. |
| `onRemoveAccount` | Called when user confirms account deletion (passes account ID) | Check if account is active (if yes, block removal with error message). Delete account from database. Return success. |
| `onUpdateSystemConfig` | Called when user changes bot state configuration (passes complete config object) | Validate config values (restore max age > 0, history limit > 0). Update configuration in database or config file. Apply changes to bot runtime if applicable. Return success/failure. |

### Empty States

Implement empty state UI for when no records exist yet:

- **No accounts configured (first-time user):** Show message "No accounts configured" with subtext "Add a BingX account to start trading". "Add Account" button is prominent. No account cards displayed.

The provided components include empty state designs for accounts tab.

## Files to Reference

- `product-plan/sections/settings/README.md` - Feature overview and design intent
- `product-plan/sections/settings/tests.md` - Test-writing instructions (use for TDD)
- `product-plan/sections/settings/components/` - React components
- `product-plan/sections/settings/types.ts` - TypeScript interfaces
- `product-plan/sections/settings/sample-data.json` - Test data
- `product-plan/sections/settings/screenshot.png` - Visual reference

## Expected User Flows

When fully implemented, users should be able to complete these flows:

### Flow 1: Add New BingX Account for Trading

1. User navigates to `/settings` (opens on Accounts tab by default)
2. User clicks "Add Account" button
3. Add Account Modal opens with form fields
4. User enters BingX API Key and API Secret (secret field is masked)
5. User selects Mode: "Demo" or "Live" via radio buttons
6. User clicks "Add" button
7. Backend validates credentials and stores account securely
8. Modal closes, success notification appears
9. New account card appears in the accounts list showing masked credentials
10. **Outcome:** User has successfully configured a trading account for the bot to use

### Flow 2: Test Connection to Verify Credentials

1. User sees account card for their BingX account
2. User clicks "Test Connection" button
3. Button shows loading state: "Testing..."
4. Backend makes test API call to BingX to verify credentials
5. Connection succeeds, success notification appears: "✅ Connection successful"
6. Account card updates connection status to "Connected" with timestamp
7. **Outcome:** User has verified their API credentials are valid and working

### Flow 3: Edit Account Credentials

1. User clicks "Edit" button on an account card
2. Edit Account Modal opens pre-filled with current API key and masked secret
3. User updates API Key to new value
4. User enters new API Secret (field shows masked input)
5. User clicks "Save"
6. Backend validates and updates credentials in database
7. Modal closes, success notification: "Account updated successfully"
8. Account card reflects updated information
9. **Outcome:** User has safely updated their exchange API credentials

### Flow 4: Switch Active Account for Trading

1. User has 2 accounts configured: Account 1 (Demo, currently active), Account 2 (Live, inactive)
2. User wants to switch bot to trade on Account 2
3. User clicks "Set Active" button on Account 2 card
4. Confirmation dialog appears: "Switching active account will change which account the bot uses for trading. Are you sure?"
5. User clicks "Confirm"
6. Backend sets Account 2 as active, Account 1 as inactive
7. Account 2 card now shows "ACTIVE" badge
8. Account 1 "ACTIVE" badge is removed, "Set Active" button appears
9. Success notification: "Active account changed"
10. **Outcome:** Bot will now trade using Account 2 credentials

### Flow 5: Remove Unused Account

1. User has Account 3 that is no longer needed (not active)
2. User clicks "Remove" button on Account 3 card
3. Confirmation dialog appears: "Are you sure you want to remove this account? This action cannot be undone."
4. User clicks "Confirm"
5. Backend deletes account from database
6. Account 3 card disappears from list
7. Success notification: "Account removed"
8. **Outcome:** Unused account has been safely deleted

### Flow 6: Update Bot State Configuration

1. User clicks "System" tab in settings
2. User sees Bot State Config section with current settings
3. User changes "Restore Max Age" from 24 to 48 hours
4. User toggles "Load History on Start" to OFF
5. User changes "History Limit" from 100 to 200 trades
6. User clicks "Save" (or changes auto-save)
7. Backend validates and updates configuration
8. Success notification: "Configuration updated"
9. **Outcome:** Bot behavior settings have been updated

### Flow 7: View System Version and Uptime Information

1. User clicks "About" tab in settings
2. User sees Version Info section displaying:
   - Btcbot version: v1.2.3
   - Backend: Python 3.11
   - Database: PostgreSQL 15.2
3. User sees Uptime section displaying:
   - Bot running time: 3 days 5 hours
   - Last restart: Jan 1, 2025 10:00 AM
4. **Outcome:** User can check version for troubleshooting and monitor bot uptime

## Done When

- [ ] Tests written for key user flows (success and failure paths)
- [ ] All tests pass
- [ ] Settings page renders with tab navigation (Accounts, System, About)
- [ ] Accounts tab displays all configured accounts as cards
- [ ] Each account card shows: exchange name, mode badge (Demo/Live), connection status, masked API key, created date, active badge (if active), action buttons
- [ ] "Add Account" button opens Add Account Modal
- [ ] Add Account Modal allows entering API key, API secret (masked), selecting mode, and saving
- [ ] New accounts are validated and stored securely (API secret encrypted)
- [ ] "Test Connection" validates API credentials with BingX and updates status
- [ ] "Edit" opens Edit Account Modal pre-filled with current data
- [ ] Editing account updates credentials securely
- [ ] "Set Active" switches active account with confirmation dialog
- [ ] Only one account can be active at a time
- [ ] Active account is clearly indicated with badge
- [ ] "Remove" deletes account after confirmation
- [ ] Cannot remove active account (must set another as active first)
- [ ] System tab displays Bot State Config with editable fields (restore max age, load history toggle, history limit)
- [ ] System config changes are validated and saved
- [ ] About tab displays read-only system info: versions (Btcbot, backend, database) and uptime (running time, last restart)
- [ ] Empty state shows when no accounts configured: helpful message and prominent "Add Account" button
- [ ] All confirmation dialogs work correctly (account removal, set active)
- [ ] API secrets are masked in UI (show only last 4 characters of API key, hide secret entirely)
- [ ] Success/error notifications appear for all actions
- [ ] Loading states appear during async operations (test connection, add/edit/remove account)
- [ ] All user actions work end-to-end
- [ ] Matches the visual design
- [ ] Responsive on mobile, tablet, and desktop
