/**
 * Issues API endpoints
 */

import { api } from './client'

export interface Issue {
  id: number
  task_id: string
  project_id: string
  title: string
  description?: string
  status: 'open' | 'in_progress' | 'in_review' | 'blocked' | 'closed' | 'draft'
  priority: 'critical' | 'high' | 'medium' | 'low'
  created_at: string
  updated_at: string
}

export interface CreateIssueRequest {
  project_id: string
  title: string
  description?: string
  priority?: 'critical' | 'high' | 'medium' | 'low'
}

export const issuesApi = {
  list: (projectId?: string) => {
    const url = projectId ? `/issues?project_id=${projectId}` : '/issues'
    return api.get<Issue[]>(url)
  },
  get: (id: string) => api.get<Issue>(`/issues/${id}`),
  create: (data: CreateIssueRequest) => api.post<Issue>('/issues', data),
  update: (id: string, data: Partial<CreateIssueRequest>) => api.patch<Issue>(`/issues/${id}`, data),
  delete: (id: string) => api.delete(`/issues/${id}`),
}

