import apiClient from '@/lib/api';
import { LoginCredentials, AuthResponse, UserRole, User } from '../types/auth.types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Nota: El backend actual usa form data para OAuth2
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await apiClient.post<{ access_token: string; token_type: string }>(
      '/api/token',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    // TODO: Obtener datos del usuario desde endpoint separado
    // Por ahora simulamos el usuario desde el token
    const mockUser: User = {
      id: 1,
      email: credentials.email,
      name: credentials.email.split('@')[0],
      role: UserRole.OPERADOR,
      created_at: new Date().toISOString(),
    };

    return {
      access_token: response.data.access_token,
      token_type: response.data.token_type,
      user: mockUser,
    };
  },

  async logout(): Promise<void> {
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },
};
