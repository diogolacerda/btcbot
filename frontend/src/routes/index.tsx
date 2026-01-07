import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AppLayout } from '@/layouts/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { TradeHistoryPage } from '@/pages/TradeHistoryPage';
import { StrategyListPage } from '@/pages/StrategyListPage';
import { SettingsPage } from '@/pages/SettingsPage';

/**
 * Application route configuration
 *
 * Routes:
 * - /login - Public login page (no layout)
 * - / - Redirects to /dashboard
 * - /dashboard - Protected dashboard page (with AppLayout)
 * - /trade-history - Protected trade history page (with AppLayout)
 * - /strategies - Protected strategy list page (with AppLayout)
 * - /strategy - Redirects to /strategies (legacy route)
 * - /settings - Protected settings page (with AppLayout)
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
        <AppLayout>
          <DashboardPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/trade-history',
    element: (
      <ProtectedRoute>
        <AppLayout>
          <TradeHistoryPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/strategies',
    element: (
      <ProtectedRoute>
        <AppLayout>
          <StrategyListPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/strategy',
    element: <Navigate to="/strategies" replace />,
  },
  {
    path: '/settings',
    element: (
      <ProtectedRoute>
        <AppLayout>
          <SettingsPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);
