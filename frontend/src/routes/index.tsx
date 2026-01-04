import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { TradeHistoryPage } from '@/pages/TradeHistoryPage';
import { StrategyPage } from '@/pages/StrategyPage';
import { SettingsPage } from '@/pages/SettingsPage';

/**
 * Application route configuration
 *
 * Routes:
 * - /login - Public login page
 * - / - Redirects to /dashboard
 * - /dashboard - Protected dashboard page
 * - /trade-history - Protected trade history page
 * - /strategy - Protected strategy configuration page
 * - /settings - Protected settings page
 */
export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/trade-history',
    element: (
      <ProtectedRoute>
        <TradeHistoryPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/strategy',
    element: (
      <ProtectedRoute>
        <StrategyPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/settings',
    element: (
      <ProtectedRoute>
        <SettingsPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);
