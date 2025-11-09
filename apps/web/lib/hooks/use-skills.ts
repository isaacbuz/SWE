/**
 * React Query hooks for Skills API
 */
'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { skillsApi, Skill, SkillDetail, SkillExecutionRequest, SkillInstallation } from '@/lib/api/skills'

// Query keys
export const skillsKeys = {
  all: ['skills'] as const,
  lists: () => [...skillsKeys.all, 'list'] as const,
  list: (filters?: Record<string, any>) => [...skillsKeys.lists(), filters] as const,
  details: () => [...skillsKeys.all, 'detail'] as const,
  detail: (id: string) => [...skillsKeys.details(), id] as const,
  installed: () => [...skillsKeys.all, 'installed'] as const,
  reviews: (id: string) => [...skillsKeys.all, 'reviews', id] as const,
  analytics: (id: string) => [...skillsKeys.all, 'analytics', id] as const,
}

/**
 * Hook to list skills with filtering
 */
export function useSkills(params?: {
  category?: string;
  tags?: string[];
  search?: string;
  visibility?: string;
  status?: string;
  sort?: string;
  order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: skillsKeys.list(params),
    queryFn: () => skillsApi.listSkills(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook to get skill details
 */
export function useSkill(id: string) {
  return useQuery({
    queryKey: skillsKeys.detail(id),
    queryFn: () => skillsApi.getSkill(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook to list installed skills
 */
export function useInstalledSkills() {
  return useQuery({
    queryKey: skillsKeys.installed(),
    queryFn: () => skillsApi.listInstalledSkills(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Hook to get skill reviews
 */
export function useSkillReviews(skillId: string, params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: skillsKeys.reviews(skillId),
    queryFn: () => skillsApi.getSkillReviews(skillId, params),
    enabled: !!skillId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook to get skill analytics
 */
export function useSkillAnalytics(skillId: string, params?: { start_date?: string; end_date?: string }) {
  return useQuery({
    queryKey: skillsKeys.analytics(skillId),
    queryFn: () => skillsApi.getSkillAnalytics(skillId, params),
    enabled: !!skillId,
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

/**
 * Hook to create a skill
 */
export function useCreateSkill() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: skillsApi.createSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillsKeys.lists() })
    },
  })
}

/**
 * Hook to update a skill
 */
export function useUpdateSkill() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => skillsApi.updateSkill(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: skillsKeys.detail(variables.id) })
      queryClient.invalidateQueries({ queryKey: skillsKeys.lists() })
    },
  })
}

/**
 * Hook to execute a skill
 */
export function useExecuteSkill() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ skillId, request }: { skillId: string; request: SkillExecutionRequest }) =>
      skillsApi.executeSkill(skillId, request),
    onSuccess: (_, variables) => {
      // Invalidate skill detail to refresh execution count
      queryClient.invalidateQueries({ queryKey: skillsKeys.detail(variables.skillId) })
      queryClient.invalidateQueries({ queryKey: skillsKeys.analytics(variables.skillId) })
    },
  })
}

/**
 * Hook to install a skill
 */
export function useInstallSkill() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ skillId, options }: { skillId: string; options?: { version?: string; auto_update?: boolean } }) =>
      skillsApi.installSkill(skillId, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillsKeys.installed() })
      queryClient.invalidateQueries({ queryKey: skillsKeys.lists() })
    },
  })
}

/**
 * Hook to uninstall a skill
 */
export function useUninstallSkill() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (skillId: string) => skillsApi.uninstallSkill(skillId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillsKeys.installed() })
      queryClient.invalidateQueries({ queryKey: skillsKeys.lists() })
    },
  })
}

