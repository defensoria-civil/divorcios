import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { Dashboard } from '@/features/metrics/components/Dashboard';
import { DashboardLayout } from '@/shared/components/Layout/DashboardLayout';

// Placeholder pages
function CasesPage() {
  return <div>Casos (En desarrollo)</div>;
}

function UsersPage() {
  return <div>Usuarios (En desarrollo)</div>;
}

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
          <CasesPage />
        </DashboardLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/users',
    element: (
      <ProtectedRoute>
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
