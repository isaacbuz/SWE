/**
 * Projects API endpoints
 */

import { api } from './client'

export interface Project {
  id: number
  project_id: string
  name: string
  description?: string
  slug: string
  repository_url?: string
  repository_provider?: 'github' | 'gitlab' | 'bitbucket'
  status: 'active' | 'archived' | 'deleted'
  owner_id: number
  created_at: string
  updated_at: string
}

export interface CreateProjectRequest {
  name: string
  description?: string
  repository_url?: string
  repository_provider?: 'github' | 'gitlab' | 'bitbucket'
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  repository_url?: string
  status?: 'active' | 'archived' | 'deleted'
}

export const projectsApi = {
  list: () => api.get<Project[]>('/projects'),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: CreateProjectRequest) => api.post<Project>('/projects', data),
  update: (id: string, data: UpdateProjectRequest) => api.patch<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
}

