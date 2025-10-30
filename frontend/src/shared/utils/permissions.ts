import { UserRole, Permission } from '@/features/auth/types/auth.types';

export const ROLE_PERMISSIONS: Record<UserRole, Permission> = {
  [UserRole.OPERADOR]: {
    canViewAllCases: false,
    canEditCases: true,
    canDeleteCases: false,
    canAssignCases: false,
    canInterveneCases: true,
    canViewUsers: false,
    canCreateUsers: false,
    canEditUsers: false,
    canDeleteUsers: false,
    canViewMetrics: true,
    canViewSystemHealth: false,
    canEditConfiguration: false,
    canExportData: true,
  },
  [UserRole.SUPERVISOR]: {
    canViewAllCases: true,
    canEditCases: true,
    canDeleteCases: true,
    canAssignCases: true,
    canInterveneCases: true,
    canViewUsers: true,
    canCreateUsers: false,
    canEditUsers: false,
    canDeleteUsers: false,
    canViewMetrics: true,
    canViewSystemHealth: true,
    canEditConfiguration: false,
    canExportData: true,
  },
  [UserRole.ADMIN]: {
    canViewAllCases: true,
    canEditCases: true,
    canDeleteCases: true,
    canAssignCases: true,
    canInterveneCases: true,
    canViewUsers: true,
    canCreateUsers: true,
    canEditUsers: true,
    canDeleteUsers: true,
    canViewMetrics: true,
    canViewSystemHealth: true,
    canEditConfiguration: true,
    canExportData: true,
  },
};

export function getRolePermissions(role: UserRole): Permission {
  return ROLE_PERMISSIONS[role];
}

export function hasPermission(role: UserRole, permission: keyof Permission): boolean {
  return ROLE_PERMISSIONS[role][permission];
}
