import { useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, History, Target, Settings } from 'lucide-react';
import { AppShell, type NavigationItem } from '@/components/shell';
import { useAuth } from '@/contexts/AuthContext';

interface AppLayoutProps {
  children: React.ReactNode;
}

/**
 * AppLayout - Main application layout wrapper
 *
 * Integrates:
 * - AppShell components (sidebar, navigation, user menu)
 * - React Router (navigation and active route detection)
 * - AuthContext (user data and logout)
 *
 * Usage:
 *   <AppLayout>
 *     <YourPageContent />
 *   </AppLayout>
 */
export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  // Define navigation items with icons and active state
  const navigationItems: NavigationItem[] = [
    {
      label: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      isActive: location.pathname === '/dashboard',
    },
    {
      label: 'Trade History',
      href: '/trade-history',
      icon: History,
      isActive: location.pathname === '/trade-history',
    },
    {
      label: 'Strategy',
      href: '/strategy',
      icon: Target,
      isActive: location.pathname === '/strategy',
    },
    {
      label: 'Settings',
      href: '/settings',
      icon: Settings,
      isActive: location.pathname === '/settings',
    },
  ];

  // Handle navigation - called when user clicks a nav item
  const handleNavigate = (href: string) => {
    navigate(href);
  };

  // Handle logout - clears auth state and redirects to login
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Transform user for AppShell format
  const shellUser = user
    ? {
        name: user.email, // Using email as name for now
        avatarUrl: undefined, // No avatar support yet
      }
    : undefined;

  return (
    <AppShell
      navigationItems={navigationItems}
      user={shellUser}
      onNavigate={handleNavigate}
      onLogout={handleLogout}
    >
      {children}
    </AppShell>
  );
}
