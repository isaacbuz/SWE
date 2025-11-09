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

export interface SkillAnalytics {
  skill_id: string
  start_date?: string
  end_date?: string
  executions: number
  executions_success?: number
  installations: number
  downloads: number
  avg_rating: number
  review_count: number
  rating_breakdown?: Record<number, number>
  avg_latency_ms?: number
  p50_latency_ms?: number
  p95_latency_ms?: number
  p99_latency_ms?: number
  total_cost_usd?: number
  avg_cost_per_execution?: number
  unique_users?: number
  updated_at: string
}

export interface SkillReview {
  id: string
  skill_id: string
  user_id: string
  rating: number
  title?: string
  review_text?: string
  created_at: string
}

export interface SkillReviewCreate {
  rating: number
  title?: string
  review_text?: string
}

export interface SkillVersion {
  id: string
  skill_id: string
  version: string
  changelog?: string
  breaking_changes: boolean
  migration_guide?: string
  status: string
  created_at: string
}
