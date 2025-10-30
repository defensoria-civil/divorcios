import { useMemo } from 'react';
import { useAuthStore } from '../store/authStore';
import { Permission, PermissionKey, UserRole } from '../types/auth.types';
import { getRolePermissions } from '@/shared/utils/permissions';

export function usePermissions() {
  const { user } = useAuthStore();

  const permissions = useMemo<Permission | null>(() => {
    if (!user) return null;
    return getRolePermissions(user.role as UserRole);
  }, [user]);

  const hasPermission = (permission: PermissionKey): boolean => {
    if (!permissions) return false;
    return permissions[permission];
  };

  return {
    permissions,
    hasPermission,
  };
}
