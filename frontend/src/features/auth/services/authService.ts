import apiClient from '@/lib/api';
import { LoginCredentials, AuthResponse, UserRole, User } from '../types/auth.types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // El backend usa JSON con username
    const response = await apiClient.post<{
      access_token: string;
      token_type: string;
      user: {
        id: number;
        username: string;
        email: string;
        full_name: string;
        role: string;
      };
    }>('/api/auth/login', {
      username: credentials.username,
      password: credentials.password,
    });

    // Mapear la respuesta del backend a nuestro tipo User
    const user: User = {
      id: response.data.user.id,
      email: response.data.user.email,
      name: response.data.user.full_name || response.data.user.username,
      role: response.data.user.role === 'admin' ? UserRole.ADMIN : UserRole.OPERADOR,
      created_at: new Date().toISOString(),
    };

    return {
      access_token: response.data.access_token,
      token_type: response.data.token_type,
      user,
    };
  },

  async logout(): Promise<void> {
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },
};
