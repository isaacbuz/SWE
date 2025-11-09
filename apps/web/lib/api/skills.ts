/**
 * Skills API Client
 */
import { Skill, SkillDetail, SkillExecutionResult, SkillInstallation, SkillAnalytics, SkillReview, SkillReviewCreate } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface SkillsListParams {
  category?: string
  tags?: string[]
  search?: string
  sort?: string
  order?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface SkillCreateInput {
  name: string
  slug: string
  description: string
  detailed_description?: string
  category: string
  tags?: string[]
  prompt_template: string
  input_schema: Record<string, any>
  output_schema: Record<string, any>
  examples?: any[]
  model_preferences?: Record<string, any>
  validation_rules?: any[]
  visibility?: 'public' | 'private' | 'unlisted'
  license?: string
  pricing_model?: 'free' | 'paid' | 'freemium'
}

export interface SkillExecutionRequest {
  skill_id: string
  inputs: Record<string, any>
  context?: Record<string, any>
}


async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}/api/v1${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || error.message || 'Request failed')
  }

  return response.json()
}

export const skillsApi = {
  async listSkills(params: SkillsListParams = {}): Promise<Skill[]> {
    const queryParams = new URLSearchParams()
    if (params.category) queryParams.append('category', params.category)
    if (params.search) queryParams.append('search', params.search)
    if (params.sort) queryParams.append('sort_by', params.sort)
    if (params.order) queryParams.append('sort_order', params.order)
    if (params.limit) queryParams.append('limit', params.limit.toString())
    if (params.offset) queryParams.append('offset', params.offset.toString())

    return apiRequest<Skill[]>(`/skills?${queryParams}`)
  },

  async getSkill(skillId: string): Promise<SkillDetail> {
    return apiRequest<SkillDetail>(`/skills/${skillId}`)
  },

  async createSkill(data: SkillCreateInput): Promise<Skill> {
    return apiRequest<Skill>('/skills', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async executeSkill(
    skillId: string,
    request: SkillExecutionRequest
  ): Promise<SkillExecutionResult> {
    return apiRequest<SkillExecutionResult>(`/skills/${skillId}/execute`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  async installSkill(skillId: string, version?: string): Promise<SkillInstallation> {
    return apiRequest<SkillInstallation>(`/skills/${skillId}/install`, {
      method: 'POST',
      body: JSON.stringify({ version }),
    })
  },

  async uninstallSkill(skillId: string): Promise<void> {
    return apiRequest<void>(`/skills/${skillId}/install`, {
      method: 'DELETE',
    })
  },

  async listInstalledSkills(): Promise<SkillInstallation[]> {
    return apiRequest<SkillInstallation[]>('/skills/installed')
  },

  async getSkillAnalytics(
    skillId: string,
    params?: { start_date?: string; end_date?: string }
  ): Promise<SkillAnalytics> {
    const queryParams = new URLSearchParams()
    if (params?.start_date) queryParams.append('start_date', params.start_date)
    if (params?.end_date) queryParams.append('end_date', params.end_date)

    return apiRequest<SkillAnalytics>(`/skills/${skillId}/analytics?${queryParams}`)
  },

  async getSkillReviews(
    skillId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<SkillReview[]> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())

    return apiRequest<SkillReview[]>(`/skills/${skillId}/reviews?${queryParams}`)
  },

  async createSkillReview(
    skillId: string,
    review: SkillReviewCreate
  ): Promise<SkillReview> {
    return apiRequest<SkillReview>(`/skills/${skillId}/reviews`, {
      method: 'POST',
      body: JSON.stringify(review),
    })
  },
}
