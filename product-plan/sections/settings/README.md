# Settings

## Overview

The Settings section provides system-level configuration management including BingX account connections, bot state configuration, and system information. Users can manage multiple exchange accounts (demo/live), configure bot behavior settings that are currently environment variables, and view version and uptime information across three organized tabs.

## User Flows

- View all connected BingX accounts with status, mode (demo/live), and details
- Add new BingX account via modal (API key/secret, demo or live mode selection)
- Test connection to validate API credentials with BingX
- Edit existing account API credentials
- Set active account to switch bot trading to a different account
- Remove account with confirmation
- Switch between tabs (Accounts, System, About)
- View and update bot state configuration (restore max age, load history on start toggle, history limit)
- View system information (Btcbot version, backend/database versions)
- View uptime metrics (bot running time, last restart timestamp)

## Design Decisions

**Tab Organization:**
- Three clear sections: Accounts (most common), System (advanced), About (informational)
- Tab navigation at top for easy switching
- Each tab focused on a specific aspect of configuration

**Account Management:**
- Card layout for accounts (one card per account)
- Visual distinction between demo and live accounts with badges
- Connection status clearly displayed (✅ Connected)
- Masked API keys for security (show only last 4 characters)
- Active account highlighted or badged

**Security Considerations:**
- API secrets are masked in display (show only as asterisks)
- Test connection feature validates credentials without exposing sensitive data
- Confirmation dialogs for account removal
- Warning when switching active account (affects live trading)

**System Configuration:**
- Read-mostly settings that were previously environment variables
- Clear labels and helpful descriptions for each setting
- Immediate save (or save button) for changes

**About Section:**
- Read-only information
- Version numbers for troubleshooting
- Uptime metrics for monitoring bot health

## Data Used

**Entities:**
- `Account` - BingX account with API credentials, mode (demo/live), connection status, active flag
- `SystemConfig` - Bot state configuration (restore max age, load history settings)
- `SystemInfo` - Read-only version and uptime information

**From global model:**
- Links to bot status (which account is actively trading)
- May reference trading history for account-specific data

## Visual Reference

See `screenshot.png` for the target UI design.

## Components Provided

- `Settings` - Main container with tab navigation
- `AccountCard` - Individual account display with actions (test, edit, set active, remove)
- `AddAccountModal` - Form to add new BingX account with API credentials
- `EditAccountModal` - Form to edit existing account credentials
- `ConfirmDialog` - Reusable confirmation for account removal and active account changes

## Callback Props

| Callback | Description |
|----------|-------------|
| `onAddAccount` | Called when user submits new account form (passes account data without ID or timestamps) |
| `onTestConnection` | Called when user clicks "Test Connection" to validate API credentials (passes account ID) |
| `onEditAccount` | Called when user saves edited account credentials (passes account ID and updated fields) |
| `onSetActiveAccount` | Called when user clicks "Set Active" to switch trading to this account (passes account ID) |
| `onRemoveAccount` | Called when user confirms account deletion (passes account ID) |
| `onUpdateSystemConfig` | Called when user changes bot state configuration (passes complete config object) |
