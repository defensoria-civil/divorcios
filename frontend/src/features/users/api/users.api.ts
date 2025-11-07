import apiClient from '@/lib/api';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: 'operator' | 'admin';
  is_active: boolean;
  created_at: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role: 'operator' | 'admin';
}

export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  role?: 'operator' | 'admin';
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  new_password: string;
}

export const usersApi = {
  /**
   * Obtiene lista de todos los usuarios
   */
  async getAll(includeInactive: boolean = false): Promise<User[]> {
    const response = await apiClient.get<User[]>('/api/users/', {
      params: { include_inactive: includeInactive },
    });
    return response.data;
  },

  /**
   * Obtiene un usuario por ID
   */
  async getById(id: number): Promise<User> {
    const response = await apiClient.get<User>(`/api/users/${id}`);
    return response.data;
  },

  /**
   * Crea un nuevo usuario
   */
  async create(data: CreateUserRequest): Promise<User> {
    const response = await apiClient.post<User>('/api/users/', data);
    return response.data;
  },

  /**
   * Actualiza un usuario existente
   */
  async update(id: number, data: UpdateUserRequest): Promise<User> {
    const response = await apiClient.put<User>(`/api/users/${id}`, data);
    return response.data;
  },

  /**
   * Elimina un usuario
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/users/${id}`);
  },

  /**
   * Cambia la contraseña de un usuario
   */
  async changePassword(id: number, data: ChangePasswordRequest): Promise<void> {
    await apiClient.post(`/api/users/${id}/change-password`, data);
  },
};
