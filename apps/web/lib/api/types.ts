/**
 * Shared TypeScript types
 */

export interface Skill {
  id: string
  name: string
  slug: string
  version: string
  description: string
  detailed_description?: string
  category: string
  tags: string[]
  author_id?: string
  author_name?: string
  download_count: number
  installation_count: number
  execution_count: number
  avg_rating: number
  review_count: number
  status: string
  visibility: 'public' | 'private' | 'unlisted'
  license: string
  pricing_model: 'free' | 'paid' | 'freemium'
  created_at: string
  updated_at: string
}

export interface SkillDetail extends Skill {
  prompt_template: string
  input_schema: Record<string, any>
  output_schema: Record<string, any>
  examples?: any[]
  model_preferences?: Record<string, any>
  validation_rules?: any[]
}

export interface SkillExecutionResult {
  execution_id: string
  skill_id: string
  skill_version: string
  status: 'success' | 'failed' | 'pending'
  inputs: Record<string, any>
  outputs?: Record<string, any>
  error_message?: string
  validation_passed: boolean
  latency_ms: number
  cost_usd: number
  cache_hit: boolean
  executed_at: string
}

export interface SkillInstallation {
  id: string
  skill_id: string
  user_id: string
  version: string
  auto_update: boolean
  enabled: boolean
  installed_at: string
  last_used_at?: string
  use_count: number
}
