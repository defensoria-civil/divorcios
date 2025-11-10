import apiClient from '@/lib/api';
import { Case, CaseDetail, CaseFilters, PaginatedResponse } from '../types/case.types';

export const casesApi = {
  /**
   * Obtiene lista de casos con paginación y filtros
   */
  async getAll(filters?: CaseFilters): Promise<PaginatedResponse<Case>> {
    const params: any = {
      page: filters?.page || 1,
      page_size: filters?.pageSize || 50,
    };

    if (filters?.status) {
      params.status = filters.status;
    }

    if (filters?.type) {
      params.type = filters.type;
    }

    if (filters?.search) {
      params.search = filters.search;
    }

    const response = await apiClient.get<PaginatedResponse<Case>>('/api/cases/', { params });
    return response.data;
  },

  /**
   * Obtiene detalle completo de un caso con mensajes
   */
  async getById(id: number): Promise<CaseDetail> {
    const response = await apiClient.get<CaseDetail>(`/api/cases/${id}`);
    return response.data;
  },

  /**
   * Obtiene estadísticas resumen de casos
   */
  async getStats(): Promise<{
    total_cases: number;
    recent_cases_7d: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
  }> {
    const response = await apiClient.get('/api/cases/stats/summary');
    return response.data;
  },

  /**
   * Actualiza campos específicos de un caso
   */
  async updateCase(id: number, updates: Record<string, any>): Promise<{
    message: string;
    updated_fields: string[];
    case_id: number;
  }> {
    const response = await apiClient.patch(`/api/cases/${id}`, updates);
    return response.data;
  },

  /**
   * Valida los datos del caso antes de generar PDF
   */
  async validateCase(id: number): Promise<{
    case_id: number;
    is_valid: boolean;
    complete_fields: Array<{field: string; label: string; value: string | null}>;
    missing_fields: Array<{field: string; label: string; value: string | null}>;
    optional_fields: Array<{field: string; label: string; value: any}>;
    completion_percentage: number;
  }> {
    const response = await apiClient.get(`/api/cases/${id}/validate`);
    return response.data;
  },

  /**
   * Obtiene la URL de un documento (DNI o acta de matrimonio)
   */
  getDocumentUrl(id: number, docType: 'dni' | 'marriage_cert'): string {
    return `/api/cases/${id}/documents/${docType}`;
  },

  /**
   * Enviar solicitud de documentación por WhatsApp (operador)
   */
  async requestDocs(id: number): Promise<{ sent: boolean }> {
    const response = await apiClient.post(`/api/cases/${id}/request-docs`);
    return response.data;
  },

  /**
   * Descarga PDF de demanda de divorcio
   */
  async downloadPetition(id: number): Promise<Blob> {
    const response = await apiClient.get(`/api/cases/${id}/petition.pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
