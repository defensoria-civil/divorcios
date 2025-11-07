export interface MetricsSummary {
  total_cases: number;
  recent_cases_7d: number;
  recent_cases_30d: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

export interface MetricsByStatus {
  status: string;
  count: number;
  percent: number;
}

export interface MetricsByType {
  type: string;
  count: number;
}

export interface MetricsTimeline {
  date: string;
  count: number;
}
