import apiClient from '@/lib/api';
import { MetricsSummary, MetricsByStatus, MetricsByType, MetricsTimeline } from '../types/metrics.types';

export const metricsApi = {
  /**
   * Obtiene resumen general de métricas
   */
  async getSummary(): Promise<MetricsSummary> {
    const response = await apiClient.get<MetricsSummary>('/api/metrics/summary');
    return response.data;
  },

  /**
   * Obtiene distribución de casos por estado
   */
  async getByStatus(): Promise<MetricsByStatus[]> {
    const response = await apiClient.get<MetricsByStatus[]>('/api/metrics/by_status');
    return response.data;
  },

  /**
   * Obtiene distribución de casos por tipo
   */
  async getByType(): Promise<MetricsByType[]> {
    const response = await apiClient.get<MetricsByType[]>('/api/metrics/by_type');
    return response.data;
  },

  /**
   * Obtiene timeline de casos creados por día
   */
  async getTimeline(days: number = 30): Promise<MetricsTimeline[]> {
    const response = await apiClient.get<MetricsTimeline[]>('/api/metrics/timeline', {
      params: { days },
    });
    return response.data;
  },
};
