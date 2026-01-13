# Test Instructions: Settings

These test-writing instructions are **framework-agnostic**. Adapt them to your testing setup (Jest, Vitest, Playwright, Cypress, React Testing Library, RSpec, Minitest, PHPUnit, etc.).

## Overview

The Settings section provides system-level configuration including BingX account management, bot state configuration, and system information. Tests should verify that users can safely manage exchange accounts, update system settings, and view version/uptime information across the three organized tabs (Accounts, System, About).

---

## User Flow Tests

### Flow 1: View All Connected Accounts

**Scenario:** User opens settings to review their configured BingX accounts

#### Success Path

**Setup:**
- User is authenticated
- User has 2 accounts configured:
  - Account 1: Demo mode, active, connected
  - Account 2: Live mode, inactive, connected

**Steps:**
1. User navigates to `/settings`
2. Settings page opens on Accounts tab by default
3. User sees list of account cards

**Expected Results:**
- [ ] Settings page loads with tab navigation showing: "Accounts", "System", "About"
- [ ] "Accounts" tab is selected/active by default
- [ ] Two account cards are displayed
- [ ] Account 1 card shows:
  - Exchange name: "BingX"
  - Mode badge: "Demo" (with appropriate color/style)
  - Connection status: "✅ Connected" (green check or success indicator)
  - Masked API key: "sk_****1234" (only last 4 chars visible)
  - Created date: e.g., "Created: Jan 1, 2025"
  - "ACTIVE" badge or indicator showing this is the active account
  - Action buttons: "Test Connection", "Edit", "Remove" (no "Set Active" since already active)
- [ ] Account 2 card shows:
  - Mode badge: "Live" (distinct from demo)
  - Connection status: "✅ Connected"
  - Masked API key
  - Created date
  - NO active badge
  - Action buttons: "Test Connection", "Edit", "Set Active", "Remove"
- [ ] "Add Account" button is visible at top or bottom of accounts list

#### Failure Path: No Accounts Configured

**Setup:**
- User has no accounts configured yet (first-time setup)

**Steps:**
1. User navigates to `/settings`

**Expected Results:**
- [ ] Accounts tab shows empty state: "No accounts configured"
- [ ] Helpful message: "Add a BingX account to start trading"
- [ ] "Add Account" button is prominent and visible
- [ ] No account cards displayed

---

### Flow 2: Add New BingX Account

**Scenario:** User wants to add a new exchange account for trading

#### Success Path

**Setup:**
- User has valid BingX API key and secret

**Steps:**
1. User is on Accounts tab
2. User clicks "Add Account" button
3. Add Account Modal opens
4. User enters API Key: "sk_test_1234567890abcdef"
5. User enters API Secret: "secret_test_0987654321fedcba" (input is masked)
6. User selects Mode: "Demo" (radio button)
7. Exchange selector shows "BingX" (for MVP, may be read-only)
8. User clicks "Add" or "Save" button

**Expected Results:**
- [ ] "Add Account" button triggers modal open
- [ ] Modal displays with heading "Add BingX Account"
- [ ] Form fields:
  - API Key input (text, required)
  - API Secret input (password/masked, required)
  - Mode selector: Radio buttons "Demo" and "Live"
  - Exchange selector: "BingX" (may be read-only dropdown or label for MVP)
- [ ] User can enter API credentials (API Secret field shows dots/asterisks as user types)
- [ ] Selecting "Demo" radio button highlights it, deselects "Live"
- [ ] Clicking "Add" button validates fields:
  - API Key is not empty
  - API Secret is not empty
  - Mode is selected
- [ ] If validation passes, `onAddAccount` callback is called with account data:
  - `{ exchange: 'BingX', mode: 'demo', apiKey: 'sk_test_1234...', apiSecretMasked: 'secret_test_...' }`
- [ ] Loading state appears on button: "Adding..."
- [ ] Modal closes after successful addition
- [ ] Success toast notification: "Account added successfully"
- [ ] New account card appears in the list

#### Failure Path: Missing Required Fields

**Setup:**
- User leaves fields empty

**Steps:**
1. User opens Add Account modal
2. User clicks "Add" without entering API Key
3. Validation runs

**Expected Results:**
- [ ] Validation error appears below API Key field: "API Key is required"
- [ ] Field border turns red
- [ ] Modal does not close
- [ ] `onAddAccount` is not called

#### Failure Path: Invalid API Credentials (detected on add)

**Setup:**
- User enters invalid API credentials

**Steps:**
1. User fills form with invalid credentials
2. User clicks "Add"
3. Backend validates and returns error

**Expected Results:**
- [ ] Error notification: "Invalid API credentials. Please check and try again."
- [ ] Modal remains open with form data preserved
- [ ] User can correct and retry

---

### Flow 3: Test Connection for an Account

**Scenario:** User wants to verify that API credentials are working

#### Success Path

**Setup:**
- Account exists with valid credentials

**Steps:**
1. User sees account card
2. User clicks "Test Connection" button
3. Backend validates credentials with BingX API

**Expected Results:**
- [ ] "Test Connection" button shows loading state: "Testing..." or spinner icon
- [ ] Button is disabled during test
- [ ] `onTestConnection` callback is called with account ID
- [ ] After successful test, success notification: "Connection successful" or "✅ Connected"
- [ ] Button returns to enabled state
- [ ] Connection status on card may update to show last tested timestamp

#### Failure Path: Connection Test Fails

**Setup:**
- Account has invalid or expired credentials

**Steps:**
1. User clicks "Test Connection"
2. Backend test fails (e.g., API returns 401 Unauthorized)

**Expected Results:**
- [ ] Error notification: "Connection failed. Please check your API credentials."
- [ ] Connection status on card updates to "❌ Disconnected" or "Connection Failed"
- [ ] User can click "Edit" to update credentials

---

### Flow 4: Edit Account Credentials

**Scenario:** User needs to update API key or secret for an existing account

#### Success Path

**Setup:**
- Account exists with ID `account-1`

**Steps:**
1. User clicks "Edit" button on account card
2. Edit Account Modal opens pre-filled with existing data
3. User updates API Key to new value
4. User updates API Secret to new value
5. User clicks "Save"

**Expected Results:**
- [ ] "Edit" button opens Edit Account Modal
- [ ] Modal heading: "Edit BingX Account"
- [ ] Form fields pre-filled:
  - API Key shows current value
  - API Secret shows masked value (e.g., "••••••••" or placeholder "Enter new secret")
  - Mode shows current selection (Demo/Live)
  - Exchange shows "BingX"
- [ ] User can edit API Key and Secret fields
- [ ] Clicking "Save" validates and calls `onEditAccount` with `(accountId, { apiKey: 'new_key', apiSecret: 'new_secret' })`
- [ ] Loading state: "Saving..."
- [ ] Modal closes after success
- [ ] Success notification: "Account updated successfully"
- [ ] Account card reflects updated information

#### Failure Path: User Cancels Edit

**Steps:**
1. User opens Edit modal
2. User makes changes
3. User clicks "Cancel" button

**Expected Results:**
- [ ] Modal closes without saving
- [ ] `onEditAccount` is not called
- [ ] Original account data remains unchanged

---

### Flow 5: Set Active Account (Switch Trading Account)

**Scenario:** User wants to switch the bot to trade on a different account

#### Success Path

**Setup:**
- Account 1 is currently active (demo mode)
- Account 2 exists (live mode)
- Bot is currently stopped (safe to switch)

**Steps:**
1. User sees Account 2 card showing "Set Active" button
2. User clicks "Set Active" button
3. Confirmation dialog appears
4. Dialog explains: "Switching active account will change which account the bot uses for trading. Are you sure?"
5. User clicks "Confirm"

**Expected Results:**
- [ ] "Set Active" button triggers confirmation dialog
- [ ] Dialog heading: "Set Active Account"
- [ ] Dialog message clearly explains consequences: "This will switch bot trading to this account"
- [ ] Dialog has "Cancel" and "Confirm" buttons
- [ ] Clicking "Confirm" calls `onSetActiveAccount(accountId)`
- [ ] Loading state during action
- [ ] After success:
  - Account 2 card now shows "ACTIVE" badge
  - Account 1 card "ACTIVE" badge is removed
  - Account 1 now shows "Set Active" button
  - Account 2 "Set Active" button is hidden/removed
- [ ] Success notification: "Active account changed to [Account 2]"

#### Failure Path: Attempt to Switch While Bot Is Running

**Setup:**
- Bot is actively trading

**Steps:**
1. User tries to set a different account as active

**Expected Results:**
- [ ] Warning or error: "Cannot switch accounts while bot is running. Please stop the bot first."
- [ ] `onSetActiveAccount` may not be called, or backend rejects with error
- [ ] User is directed to stop bot before switching

---

### Flow 6: Remove Account

**Scenario:** User wants to delete an account they no longer need

#### Success Path

**Setup:**
- Account to remove is NOT the active account
- User has other accounts configured

**Steps:**
1. User sees account card
2. User clicks "Remove" button
3. Confirmation dialog appears
4. Dialog warns: "Are you sure you want to remove this account? This action cannot be undone."
5. User clicks "Confirm"

**Expected Results:**
- [ ] "Remove" button triggers confirmation dialog
- [ ] Dialog heading: "Remove Account"
- [ ] Dialog warning message explains action is permanent
- [ ] Dialog has "Cancel" and "Confirm" buttons (Confirm may be red/destructive style)
- [ ] Clicking "Confirm" calls `onRemoveAccount(accountId)`
- [ ] Loading state during deletion
- [ ] After success:
  - Account card is removed from list
  - Success notification: "Account removed"
  - If this was the last account, empty state appears

#### Failure Path: Attempt to Remove Active Account

**Setup:**
- User tries to remove the currently active account

**Steps:**
1. User clicks "Remove" on active account card

**Expected Results:**
- [ ] Error or warning: "Cannot remove active account. Please set another account as active first."
- [ ] Remove action is blocked
- [ ] User must set a different account as active before removing this one

---

### Flow 7: Switch to System Tab and Update Bot Configuration

**Scenario:** User wants to change bot state configuration settings

#### Success Path

**Setup:**
- User is on Accounts tab
- Current system config: Restore Max Age = 24 hours, Load History on Start = true, History Limit = 100

**Steps:**
1. User clicks "System" tab
2. System tab content loads
3. User sees Bot State Config section
4. User changes Restore Max Age from "24" to "48" hours
5. User toggles Load History on Start to OFF
6. User changes History Limit from "100" to "200"
7. User clicks "Save" or changes auto-save

**Expected Results:**
- [ ] Clicking "System" tab switches view to System configuration
- [ ] Tab indicator shows "System" as active
- [ ] Bot State Config section displays:
  - "Restore Max Age" input field showing "24" (in hours)
  - "Load History on Start" toggle switch showing ON
  - "History Limit" input field showing "100"
- [ ] User can edit Restore Max Age input to "48"
- [ ] User can toggle Load History switch to OFF
- [ ] User can edit History Limit to "200"
- [ ] Clicking "Save" (if present) or auto-save triggers `onUpdateSystemConfig` with:
  - `{ restoreMaxAge: 48, loadHistoryOnStart: false, historyLimit: 200 }`
- [ ] Success notification: "Configuration updated"

#### Validation Path: Invalid Input

**Steps:**
1. User enters negative value in Restore Max Age: "-5"
2. User tries to save

**Expected Results:**
- [ ] Validation error: "Restore Max Age must be a positive number"
- [ ] Field border turns red
- [ ] Save is blocked until fixed

---

### Flow 8: View System Information in About Tab

**Scenario:** User wants to check bot version and uptime

#### Success Path

**Setup:**
- Btcbot version: v1.2.3
- Backend version: Python 3.11
- Database: PostgreSQL 15.2
- Bot running time: 3 days 5 hours
- Last restart: Jan 1, 2025 10:00 AM

**Steps:**
1. User clicks "About" tab
2. About tab content loads

**Expected Results:**
- [ ] Clicking "About" tab switches view
- [ ] Tab indicator shows "About" as active
- [ ] **Version Info section** displays:
  - Btcbot version: "v1.2.3"
  - Backend version: "Python 3.11"
  - Database version: "PostgreSQL 15.2"
- [ ] **Uptime section** displays:
  - Bot running time: "3 days 5 hours" (human-readable format)
  - Last restart: "Jan 1, 2025 10:00 AM"
- [ ] All information is read-only (no edit fields)
- [ ] Information is formatted clearly and easy to read

---

## Empty State Tests

### No Accounts Configured

**Scenario:** First-time user has not added any accounts

**Setup:**
- Accounts array is empty: `[]`

**Expected Results:**
- [ ] Accounts tab shows empty state message: "No accounts configured"
- [ ] Helpful subtext: "Add a BingX account to start trading"
- [ ] "Add Account" button is prominent
- [ ] No account cards displayed

---

## Component Interaction Tests

### Settings Component (Tab Navigation)

**Renders correctly:**
- [ ] Displays three tabs: "Accounts", "System", "About"
- [ ] "Accounts" tab is active by default
- [ ] Tab content switches when clicking different tabs

**User interactions:**
- [ ] Clicking "System" tab shows system configuration content
- [ ] Clicking "About" tab shows version and uptime info
- [ ] Active tab is visually indicated (highlighted, underlined, or border)
- [ ] Content for inactive tabs is hidden

### AccountCard Component

**Renders correctly:**
- [ ] Displays exchange name "BingX"
- [ ] Shows mode badge ("Demo" or "Live") with distinct styling
- [ ] Connection status displayed: "✅ Connected" or "❌ Disconnected"
- [ ] Masked API Key: shows only last 4 characters
- [ ] Created date formatted: "Created: Jan 1, 2025"
- [ ] "ACTIVE" badge shows on active account
- [ ] Action buttons: "Test Connection", "Edit", "Set Active" (if not active), "Remove"

**User interactions:**
- [ ] Clicking "Test Connection" calls `onTestConnection(accountId)`
- [ ] Clicking "Edit" opens Edit Account Modal
- [ ] Clicking "Set Active" opens confirmation then calls `onSetActiveAccount(accountId)`
- [ ] Clicking "Remove" opens confirmation then calls `onRemoveAccount(accountId)`
- [ ] Buttons show loading states during actions

### AddAccountModal Component

**Renders correctly:**
- [ ] Modal heading: "Add BingX Account"
- [ ] API Key input field (text type)
- [ ] API Secret input field (password type, masked)
- [ ] Mode selector: Radio buttons for "Demo" and "Live"
- [ ] Exchange selector: "BingX" (dropdown or label)
- [ ] "Add" button and "Cancel" button

**User interactions:**
- [ ] Typing in API Secret field shows masked characters (dots)
- [ ] Selecting "Demo" or "Live" radio button updates selection
- [ ] Clicking "Cancel" closes modal without saving
- [ ] Clicking "Add" validates fields and calls `onAddAccount` if valid
- [ ] Validation errors display for empty required fields

### EditAccountModal Component

**Renders correctly:**
- [ ] Modal heading: "Edit BingX Account"
- [ ] API Key input pre-filled with current value
- [ ] API Secret input shows masked placeholder or editable field
- [ ] Mode shows current selection
- [ ] Exchange shows "BingX"
- [ ] "Save" and "Cancel" buttons

**User interactions:**
- [ ] User can edit API Key and Secret
- [ ] Clicking "Save" validates and calls `onEditAccount(accountId, updates)`
- [ ] Clicking "Cancel" closes modal without changes

### ConfirmDialog Component

**Renders correctly:**
- [ ] Heading shows action (e.g., "Set Active Account", "Remove Account")
- [ ] Message explains consequences
- [ ] "Cancel" and "Confirm" buttons

**User interactions:**
- [ ] Clicking "Cancel" closes dialog without action
- [ ] Clicking "Confirm" triggers associated callback
- [ ] Pressing Escape key closes dialog (cancel behavior)

---

## Edge Cases

- [ ] **Many accounts (10+):** List scrolls or paginates appropriately, no performance issues
- [ ] **Very long API key:** Masked key displays with ellipsis if needed, doesn't break layout
- [ ] **Rapid tab switching:** Content loads smoothly without flickering or broken state
- [ ] **Test connection during network loss:** Error handling, timeout, user can retry
- [ ] **Attempt to add duplicate account:** Validation or warning: "Account with this API Key already exists"
- [ ] **Switching active account while trades are open:** Warning or block action until trades close
- [ ] **System config with extreme values:** Restore Max Age = 1000 hours or History Limit = 10,000 (validate or warn if unreasonable)

---

## Accessibility Checks

- [ ] Tab navigation is keyboard accessible (Tab to focus, Enter to switch tabs)
- [ ] Form inputs in modals have associated labels
- [ ] Radio buttons keyboard navigable (arrow keys)
- [ ] Confirm dialogs trap focus
- [ ] Success/error notifications announced to screen readers
- [ ] "Set Active" and "Remove" actions have clear accessible labels
- [ ] Connection status has text, not just icon (screen reader friendly)

---

## Sample Test Data

```typescript
// Example test data - Accounts
const mockAccounts: Account[] = [
  {
    id: 'account-1',
    exchange: 'BingX',
    mode: 'demo',
    apiKey: 'sk_test_1234567890abcdef',
    apiSecretMasked: '••••••••••••••••fedcba',
    connectionStatus: 'connected',
    isActive: true,
    createdAt: '2025-01-01T10:00:00Z',
    lastTestedAt: '2025-01-03T15:00:00Z'
  },
  {
    id: 'account-2',
    exchange: 'BingX',
    mode: 'live',
    apiKey: 'sk_live_abcdef1234567890',
    apiSecretMasked: '••••••••••••••••567890',
    connectionStatus: 'connected',
    isActive: false,
    createdAt: '2025-01-02T12:00:00Z',
    lastTestedAt: '2025-01-03T14:00:00Z'
  }
];

// Example test data - System Config
const mockSystemConfig: SystemConfig = {
  restoreMaxAge: 24,
  loadHistoryOnStart: true,
  historyLimit: 100
};

// Example test data - System Info
const mockSystemInfo: SystemInfo = {
  versions: {
    btcbot: 'v1.2.3',
    backend: 'Python 3.11',
    database: 'PostgreSQL 15.2'
  },
  uptime: {
    runningTime: '3 days 5 hours',
    lastRestartAt: '2025-01-01T10:00:00Z'
  }
};

// Example test data - Empty state
const mockEmptyAccounts = [];
```

---

## Notes for Test Implementation

- Mock API calls for account management actions (add, edit, test, remove, set active)
- Test each callback prop is called with correct arguments
- Verify tab switching updates content correctly
- Test confirmation dialogs prevent accidental destructive actions (remove account)
- Test validation for account credentials and system config inputs
- Ensure loading states appear during async operations
- Test that masked API secrets never expose full secret in UI
- Verify active account badge updates correctly when setting new active account
- Test error handling for failed API calls (connection test, add account, etc.)
- **Always test empty state** - Pass empty array for accounts to verify helpful empty state appears
