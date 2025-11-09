/**
 * Skills API client and types
 */

export interface Skill {
  id: string;
  name: string;
  slug: string;
  version: string;
  description: string;
  detailed_description?: string;
  category: string;
  tags: string[];
  author_id?: string;
  author_name?: string;
  download_count: number;
  installation_count: number;
  execution_count: number;
  avg_rating: number;
  review_count: number;
  status: string;
  visibility: string;
  license: string;
  pricing_model: string;
  created_at?: string;
  updated_at?: string;
}

export interface SkillDetail extends Skill {
  prompt_template: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  examples?: Array<Record<string, any>>;
  model_preferences: Record<string, any>;
  validation_rules?: Array<Record<string, any>>;
}

export interface SkillExecutionRequest {
  skill_id: string;
  inputs: Record<string, any>;
  context?: Record<string, any>;
}

export interface SkillExecutionResult {
  execution_id: string;
  skill_id: string;
  skill_version: string;
  status: string;
  inputs: Record<string, any>;
  outputs?: Record<string, any>;
  validation_passed: boolean;
  validation_result?: Record<string, any>;
  model_id?: string;
  model_provider?: string;
  latency_ms?: number;
  tokens_input?: number;
  tokens_output?: number;
  cost_usd?: number;
  cache_hit: boolean;
  error_message?: string;
  executed_at: string;
  completed_at?: string;
}

export interface SkillInstallation {
  id: string;
  skill_id: string;
  user_id: string;
  version: string;
  auto_update: boolean;
  enabled: boolean;
  installed_at: string;
  last_used_at?: string;
  use_count: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.detail || error.message || 'Request failed');
  }

  return response.json();
}

export const skillsApi = {
  /**
   * List skills with filtering and pagination
   */
  async listSkills(params?: {
    category?: string;
    tags?: string[];
    search?: string;
    visibility?: string;
    status?: string;
    sort?: string;
    order?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
  }): Promise<Skill[]> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append('category', params.category);
    if (params?.tags) params.tags.forEach(tag => searchParams.append('tags', tag));
    if (params?.search) searchParams.append('search', params.search);
    if (params?.visibility) searchParams.append('visibility', params.visibility);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.sort) searchParams.append('sort', params.sort);
    if (params?.order) searchParams.append('order', params.order);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    return apiRequest<Skill[]>(`/skills?${searchParams.toString()}`);
  },

  /**
   * Get skill details by ID
   */
  async getSkill(id: string): Promise<SkillDetail> {
    return apiRequest<SkillDetail>(`/skills/${id}`);
  },

  /**
   * Create a new skill
   */
  async createSkill(data: {
    name: string;
    slug: string;
    description: string;
    detailed_description?: string;
    category: string;
    tags?: string[];
    prompt_template: string;
    input_schema: Record<string, any>;
    output_schema: Record<string, any>;
    examples?: Array<Record<string, any>>;
    model_preferences?: Record<string, any>;
    validation_rules?: Array<Record<string, any>>;
    visibility?: string;
    license?: string;
    pricing_model?: string;
  }): Promise<Skill> {
    return apiRequest<Skill>('/skills', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update a skill
   */
  async updateSkill(
    id: string,
    data: Partial<{
      name: string;
      description: string;
      detailed_description: string;
      category: string;
      tags: string[];
      prompt_template: string;
      input_schema: Record<string, any>;
      output_schema: Record<string, any>;
      model_preferences: Record<string, any>;
      validation_rules: Array<Record<string, any>>;
      status: string;
    }>
  ): Promise<Skill> {
    return apiRequest<Skill>(`/skills/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Execute a skill
   */
  async executeSkill(
    skillId: string,
    request: SkillExecutionRequest
  ): Promise<SkillExecutionResult> {
    return apiRequest<SkillExecutionResult>(`/skills/${skillId}/execute`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Install a skill
   */
  async installSkill(
    skillId: string,
    options?: { version?: string; auto_update?: boolean }
  ): Promise<SkillInstallation> {
    const searchParams = new URLSearchParams();
    if (options?.version) searchParams.append('version', options.version);
    if (options?.auto_update !== undefined) {
      searchParams.append('auto_update', options.auto_update.toString());
    }

    return apiRequest<SkillInstallation>(
      `/skills/${skillId}/install?${searchParams.toString()}`,
      { method: 'POST' }
    );
  },

  /**
   * Uninstall a skill
   */
  async uninstallSkill(skillId: string): Promise<void> {
    return apiRequest<void>(`/skills/${skillId}/install`, {
      method: 'DELETE',
    });
  },

  /**
   * List installed skills
   */
  async listInstalledSkills(): Promise<SkillInstallation[]> {
    return apiRequest<SkillInstallation[]>('/skills/installed');
  },

  /**
   * Get skill reviews
   */
  async getSkillReviews(
    skillId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<any[]> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    return apiRequest<any[]>(`/skills/${skillId}/reviews?${searchParams.toString()}`);
  },

  /**
   * Get skill analytics
   */
  async getSkillAnalytics(
    skillId: string,
    params?: { start_date?: string; end_date?: string }
  ): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);

    return apiRequest<any>(`/skills/${skillId}/analytics?${searchParams.toString()}`);
  },
};

