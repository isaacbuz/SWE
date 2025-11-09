/**
 * Skills API Client
 */
import { Skill, SkillDetail, SkillExecutionResult, SkillInstallation } from './types'

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

export const skillsApi = {
  async listSkills(params: SkillsListParams = {}): Promise<Skill[]> {
    const queryParams = new URLSearchParams()
    if (params.category) queryParams.append('category', params.category)
    if (params.search) queryParams.append('search', params.search)
    if (params.sort) queryParams.append('sort_by', params.sort)
    if (params.order) queryParams.append('sort_order', params.order)
    if (params.limit) queryParams.append('limit', params.limit.toString())
    if (params.offset) queryParams.append('offset', params.offset.toString())

    const response = await fetch(`${API_BASE}/api/v1/skills?${queryParams}`)
    if (!response.ok) throw new Error('Failed to fetch skills')
    return response.json()
  },

  async getSkill(skillId: string): Promise<SkillDetail> {
    const response = await fetch(`${API_BASE}/api/v1/skills/${skillId}`)
    if (!response.ok) throw new Error('Failed to fetch skill')
    return response.json()
  },

  async createSkill(data: SkillCreateInput): Promise<Skill> {
    const response = await fetch(`${API_BASE}/api/v1/skills`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create skill' }))
      throw new Error(error.detail || 'Failed to create skill')
    }
    return response.json()
  },

  async executeSkill(
    skillId: string,
    request: SkillExecutionRequest
  ): Promise<SkillExecutionResult> {
    const response = await fetch(`${API_BASE}/api/v1/skills/${skillId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Failed to execute skill')
    return response.json()
  },

  async installSkill(skillId: string, version?: string): Promise<SkillInstallation> {
    const response = await fetch(`${API_BASE}/api/v1/skills/${skillId}/install`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version }),
    })
    if (!response.ok) throw new Error('Failed to install skill')
    return response.json()
  },

  async uninstallSkill(skillId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/v1/skills/${skillId}/install`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to uninstall skill')
  },

  async listInstalledSkills(): Promise<SkillInstallation[]> {
    const response = await fetch(`${API_BASE}/api/v1/skills/installed`)
    if (!response.ok) throw new Error('Failed to fetch installed skills')
    return response.json()
  },
}

