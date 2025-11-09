'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Star, Download, Zap, Code, Play, Install, Trash2, BarChart3 } from 'lucide-react'
import { useSkill, useInstallSkill, useUninstallSkill, useInstalledSkills, useSkillReviews } from '@/lib/hooks/use-skills'
import { SkillPlayground } from '@/components/skills/skill-playground'
import { ReviewList } from '@/components/skills/review-list'
import { ReviewForm } from '@/components/skills/review-form'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils/cn'

interface SkillDetailPageProps {
  params: Promise<{ id: string }>
}

export default function SkillDetailPage({ params }: SkillDetailPageProps) {
  const { id } = use(params)
  const { data: skill, isLoading, error } = useSkill(id)
  const { data: installedSkills } = useInstalledSkills()
  const { data: reviews = [] } = useSkillReviews(id)
  const [showReviewForm, setShowReviewForm] = useState(false)
  const isInstalled = installedSkills?.some(s => s.skill_id === id)

  const installSkill = useInstallSkill()
  const uninstallSkill = useUninstallSkill()

  const handleInstall = () => {
    installSkill.mutate({ skillId: id })
  }

  const handleUninstall = () => {
    uninstallSkill.mutate(id)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse rounded bg-surface-secondary" />
        <div className="h-96 animate-pulse rounded-lg bg-surface-secondary" />
      </div>
    )
  }

  if (error || !skill) {
    return (
      <div className="space-y-6">
        <Link href="/skills">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Marketplace
          </Button>
        </Link>
        <Card className="p-6">
          <p className="text-status-error">
            {error?.message || 'Skill not found'}
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/skills">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Marketplace
          </Button>
        </Link>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-ink-primary">{skill.name}</h1>
              <Badge variant="outline">{skill.version}</Badge>
              {skill.status === 'active' && (
                <Badge className="bg-status-success/10 text-status-success border-status-success/20">
                  Active
                </Badge>
              )}
            </div>
            <p className="mt-2 text-ink-secondary">{skill.description}</p>

            {/* Stats */}
            <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-ink-tertiary">
              <div className="flex items-center gap-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span className="font-medium text-ink-primary">
                  {skill.avg_rating.toFixed(1)}
                </span>
                <span>({skill.review_count} reviews)</span>
              </div>
              <div className="flex items-center gap-1">
                <Download className="h-4 w-4" />
                <span>{skill.installation_count} installations</span>
              </div>
              <div className="flex items-center gap-1">
                <Zap className="h-4 w-4" />
                <span>{skill.execution_count} executions</span>
              </div>
              {skill.author_name && (
                <span>by {skill.author_name}</span>
              )}
            </div>

            {/* Tags */}
            {skill.tags && skill.tags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {skill.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Link href={`/skills/${id}/analytics`}>
              <Button variant="outline">
                <BarChart3 className="mr-2 h-4 w-4" />
                Analytics
              </Button>
            </Link>
            {isInstalled ? (
              <Button
                variant="outline"
                onClick={handleUninstall}
                disabled={uninstallSkill.isPending}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Uninstall
              </Button>
            ) : (
              <Button
                onClick={handleInstall}
                disabled={installSkill.isPending}
              >
                <Install className="mr-2 h-4 w-4" />
                Install
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="playground">Playground</TabsTrigger>
          <TabsTrigger value="documentation">Documentation</TabsTrigger>
          <TabsTrigger value="reviews">Reviews</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Detailed Description */}
          {skill.detailed_description && (
            <Card className="p-6">
              <h2 className="mb-4 text-xl font-semibold text-ink-primary">Description</h2>
              <div
                className="prose prose-sm max-w-none text-ink-secondary"
                dangerouslySetInnerHTML={{ __html: skill.detailed_description }}
              />
            </Card>
          )}

          {/* Examples */}
          {skill.examples && skill.examples.length > 0 && (
            <Card className="p-6">
              <h2 className="mb-4 text-xl font-semibold text-ink-primary">Examples</h2>
              <div className="space-y-4">
                {skill.examples.map((example, i) => (
                  <div key={i} className="rounded-md border border-border-default bg-surface-secondary p-4">
                    <h3 className="mb-2 font-medium text-ink-primary">
                      Example {i + 1}
                    </h3>
                    <pre className="overflow-auto text-sm">
                      {JSON.stringify(example, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Schema Info */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="p-6">
              <h2 className="mb-4 text-xl font-semibold text-ink-primary">Input Schema</h2>
              <pre className="overflow-auto rounded-md border border-border-default bg-surface-secondary p-4 text-sm">
                {JSON.stringify(skill.input_schema, null, 2)}
              </pre>
            </Card>
            <Card className="p-6">
              <h2 className="mb-4 text-xl font-semibold text-ink-primary">Output Schema</h2>
              <pre className="overflow-auto rounded-md border border-border-default bg-surface-secondary p-4 text-sm">
                {JSON.stringify(skill.output_schema, null, 2)}
              </pre>
            </Card>
          </div>
        </TabsContent>

        {/* Playground Tab */}
        <TabsContent value="playground">
          <SkillPlayground skill={skill} />
        </TabsContent>

        {/* Documentation Tab */}
        <TabsContent value="documentation" className="space-y-6">
          <Card className="p-6">
            <h2 className="mb-4 text-xl font-semibold text-ink-primary">Model Preferences</h2>
            <pre className="overflow-auto rounded-md border border-border-default bg-surface-secondary p-4 text-sm">
              {JSON.stringify(skill.model_preferences, null, 2)}
            </pre>
          </Card>

          {skill.validation_rules && skill.validation_rules.length > 0 && (
            <Card className="p-6">
              <h2 className="mb-4 text-xl font-semibold text-ink-primary">Validation Rules</h2>
              <pre className="overflow-auto rounded-md border border-border-default bg-surface-secondary p-4 text-sm">
                {JSON.stringify(skill.validation_rules, null, 2)}
              </pre>
            </Card>
          )}
        </TabsContent>

        {/* Reviews Tab */}
        <TabsContent value="reviews" className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold">Reviews</h2>
              <p className="text-sm text-muted-foreground mt-1">
                {reviews.length} {reviews.length === 1 ? 'review' : 'reviews'}
              </p>
            </div>
            <Button
              onClick={() => setShowReviewForm(!showReviewForm)}
              variant={showReviewForm ? 'outline' : 'default'}
            >
              {showReviewForm ? 'Cancel' : 'Write a Review'}
            </Button>
          </div>

          {showReviewForm && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Write a Review</h3>
              <ReviewForm
                skillId={id}
                onSuccess={() => setShowReviewForm(false)}
              />
            </Card>
          )}

          <ReviewList reviews={reviews} skillId={id} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

