export enum UserRole {
  OPERADOR = 'operador',
  SUPERVISOR = 'supervisor',
  ADMIN = 'admin',
}

export interface User {
  id: number;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Permission {
  // Casos
  canViewAllCases: boolean;
  canEditCases: boolean;
  canDeleteCases: boolean;
  canAssignCases: boolean;
  canInterveneCases: boolean;
  
  // Usuarios
  canViewUsers: boolean;
  canCreateUsers: boolean;
  canEditUsers: boolean;
  canDeleteUsers: boolean;
  
  // Sistema
  canViewMetrics: boolean;
  canViewSystemHealth: boolean;
  canEditConfiguration: boolean;
  canExportData: boolean;
}

export type PermissionKey = keyof Permission;
