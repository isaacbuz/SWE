/**
 * React Query hooks for Skills
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { skillsApi, SkillsListParams, SkillCreateInput, SkillExecutionRequest } from '../api/skills'
import { Skill, SkillDetail, SkillAnalytics, SkillReview, SkillReviewCreate } from '../api/types'

export function useSkills(params: SkillsListParams = {}) {
  return useQuery({
    queryKey: ['skills', params],
    queryFn: () => skillsApi.listSkills(params),
  })
}

export function useSkill(skillId: string | null) {
  return useQuery({
    queryKey: ['skill', skillId],
    queryFn: () => (skillId ? skillsApi.getSkill(skillId) : null),
    enabled: !!skillId,
  })
}

export function useCreateSkill() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: SkillCreateInput) => skillsApi.createSkill(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
    },
  })
}

export function useExecuteSkill() {
  return useMutation({
    mutationFn: ({ skillId, request }: { skillId: string; request: SkillExecutionRequest }) =>
      skillsApi.executeSkill(skillId, request),
  })
}

export function useInstallSkill() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ skillId, version }: { skillId: string; version?: string }) =>
      skillsApi.installSkill(skillId, version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      queryClient.invalidateQueries({ queryKey: ['installed-skills'] })
    },
  })
}

export function useUninstallSkill() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ skillId }: { skillId: string }) => skillsApi.uninstallSkill(skillId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      queryClient.invalidateQueries({ queryKey: ['installed-skills'] })
    },
  })
}

export function useInstalledSkills() {
  return useQuery({
    queryKey: ['installed-skills'],
    queryFn: () => skillsApi.listInstalledSkills(),
  })
}

export function useSkillAnalytics(
  skillId: string | null,
  params?: { start_date?: string; end_date?: string }
) {
  return useQuery({
    queryKey: ['skill-analytics', skillId, params],
    queryFn: () => (skillId ? skillsApi.getSkillAnalytics(skillId, params) : null),
    enabled: !!skillId,
  })
}

export function useSkillReviews(
  skillId: string | null,
  params?: { limit?: number; offset?: number }
) {
  return useQuery({
    queryKey: ['skill-reviews', skillId, params],
    queryFn: () => (skillId ? skillsApi.getSkillReviews(skillId, params) : []),
    enabled: !!skillId,
  })
}

export function useCreateSkillReview() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ skillId, review }: { skillId: string; review: SkillReviewCreate }) =>
      skillsApi.createSkillReview(skillId, review),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['skill-reviews', variables.skillId] })
      queryClient.invalidateQueries({ queryKey: ['skill', variables.skillId] })
    },
  })
}
