/**
 * Agents API endpoints
 */

import { api } from './client'

export interface Agent {
  id: number
  agent_id: string
  name: string
  type: string
  status: 'idle' | 'running' | 'paused' | 'error'
  created_at: string
  updated_at: string
}

export interface CreateAgentRequest {
  name: string
  type: string
  config?: Record<string, any>
}

export const agentsApi = {
  list: () => api.get<Agent[]>('/agents'),
  get: (id: string) => api.get<Agent>(`/agents/${id}`),
  create: (data: CreateAgentRequest) => api.post<Agent>('/agents', data),
  update: (id: string, data: Partial<CreateAgentRequest>) => api.patch<Agent>(`/agents/${id}`, data),
  start: (id: string) => api.post(`/agents/${id}/start`),
  cancel: (id: string) => api.post(`/agents/${id}/cancel`),
  delete: (id: string) => api.delete(`/agents/${id}`),
}

