/**
 * Analytics API endpoints
 */

import { api } from './client'

export interface DashboardOverview {
  total_projects: number
  total_agents: number
  active_issues: number
  completed_issues: number
  total_cost_usd: number
  avg_review_time_minutes: number
}

export interface TimeSeriesData {
  timestamp: string
  value: number
  label?: string
}

export const analyticsApi = {
  overview: () => api.get<DashboardOverview>('/analytics/overview'),
  projectMetrics: (projectId: string) => api.get(`/analytics/projects/${projectId}`),
  agentPerformance: () => api.get('/analytics/agents'),
  timeSeries: (metric: string, startDate: string, endDate: string) =>
    api.get<TimeSeriesData[]>(`/analytics/time-series?metric=${metric}&start=${startDate}&end=${endDate}`),
}

