import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { Dashboard } from '@/features/metrics/components/Dashboard';
import { DashboardLayout } from '@/shared/components/Layout/DashboardLayout';
import { CasesList } from '@/features/cases/components/CasesList';
import { CaseDetail } from '@/features/cases/components/CaseDetail';
import { UsersPage } from '@/features/users/components/UsersPage';
import { UserRole } from '@/features/auth/types/auth.types';

// Placeholder pages

function SettingsPage() {
  return <div>Configuración (En desarrollo)</div>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginForm />,
  },
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardLayout>
          <Dashboard />
        </DashboardLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/cases',
    element: (
      <ProtectedRoute>
        <DashboardLayout>
          <CasesList />
        </DashboardLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/cases/:id',
    element: (
      <ProtectedRoute>
        <DashboardLayout>
          <CaseDetail />
        </DashboardLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/users',
    element: (
      <ProtectedRoute requiredRole={UserRole.ADMIN}>
        <DashboardLayout>
          <UsersPage />
        </DashboardLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/settings',
    element: (
      <ProtectedRoute>
        <DashboardLayout>
          <SettingsPage />
        </DashboardLayout>
      </ProtectedRoute>
    ),
  },
]);
