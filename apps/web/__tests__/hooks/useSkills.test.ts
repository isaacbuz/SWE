/**
 * Tests for Skills React Query hooks
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useSkills, useSkill, useInstallSkill, useExecuteSkill } from '@/lib/hooks/use-skills'
import { skillsApi } from '@/lib/api/skills'

// Mock the API client
vi.mock('@/lib/api/skills', () => ({
  skillsApi: {
    listSkills: vi.fn(),
    getSkill: vi.fn(),
    installSkill: vi.fn(),
    executeSkill: vi.fn(),
  },
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useSkills', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches skills successfully', async () => {
    const mockSkills = [
      {
        id: 'skill-1',
        name: 'Test Skill',
        slug: 'test-skill',
        version: '1.0.0',
        description: 'A test skill',
        category: 'CODE_GENERATION',
        tags: ['test'],
        download_count: 0,
        installation_count: 0,
        execution_count: 0,
        avg_rating: 0,
        review_count: 0,
        status: 'active',
        visibility: 'public',
        license: 'MIT',
        pricing_model: 'free',
      },
    ]

    vi.mocked(skillsApi.listSkills).mockResolvedValue(mockSkills)

    const { result } = renderHook(() => useSkills(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSkills)
    expect(skillsApi.listSkills).toHaveBeenCalled()
  })

  it('handles error states', async () => {
    const error = new Error('Failed to fetch')
    vi.mocked(skillsApi.listSkills).mockRejectedValue(error)

    const { result } = renderHook(() => useSkills(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeTruthy()
  })

  it('passes filters to API', async () => {
    vi.mocked(skillsApi.listSkills).mockResolvedValue([])

    const { result } = renderHook(
      () => useSkills({ category: 'CODE_GENERATION', search: 'test' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(skillsApi.listSkills).toHaveBeenCalledWith({
      category: 'CODE_GENERATION',
      search: 'test',
    })
  })
})

describe('useSkill', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches skill details successfully', async () => {
    const mockSkill = {
      id: 'skill-1',
      name: 'Test Skill',
      prompt_template: 'Template',
      input_schema: {},
      output_schema: {},
      model_preferences: {},
    }

    vi.mocked(skillsApi.getSkill).mockResolvedValue(mockSkill as any)

    const { result } = renderHook(() => useSkill('skill-1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSkill)
  })

  it('does not fetch when id is empty', () => {
    const { result } = renderHook(() => useSkill(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
  })
})

describe('useInstallSkill', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('installs skill successfully', async () => {
    const mockInstallation = {
      id: 'install-1',
      skill_id: 'skill-1',
      user_id: 'user-1',
      version: '1.0.0',
      auto_update: true,
      enabled: true,
      installed_at: new Date().toISOString(),
      use_count: 0,
    }

    vi.mocked(skillsApi.installSkill).mockResolvedValue(mockInstallation as any)

    const { result } = renderHook(() => useInstallSkill(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ skillId: 'skill-1' })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(skillsApi.installSkill).toHaveBeenCalledWith('skill-1', undefined)
  })
})

describe('useExecuteSkill', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('executes skill successfully', async () => {
    const mockResult = {
      execution_id: 'exec-1',
      skill_id: 'skill-1',
      skill_version: '1.0.0',
      status: 'success',
      inputs: { name: 'test' },
      outputs: { result: 'output' },
      validation_passed: true,
      latency_ms: 100,
      cost_usd: 0.001,
      cache_hit: false,
      executed_at: new Date().toISOString(),
    }

    vi.mocked(skillsApi.executeSkill).mockResolvedValue(mockResult as any)

    const { result } = renderHook(() => useExecuteSkill(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      skillId: 'skill-1',
      request: {
        skill_id: 'skill-1',
        inputs: { name: 'test' },
        context: {},
      },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(skillsApi.executeSkill).toHaveBeenCalled()
  })
})

