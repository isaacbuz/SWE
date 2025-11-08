'use client'

import Link from 'next/link'
import { Star, Download, Code, Zap, Clock } from 'lucide-react'
import { Skill } from '@/lib/api/skills'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils/cn'

interface SkillCardProps {
  skill: Skill
  installed?: boolean
  onInstall?: (skillId: string) => void
  onUninstall?: (skillId: string) => void
}

const categoryIcons: Record<string, any> = {
  CODE_GENERATION: Code,
  TESTING: Zap,
  SECURITY: Code,
  DOCUMENTATION: Code,
  CODE_REVIEW: Code,
}

const categoryColors: Record<string, string> = {
  CODE_GENERATION: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  TESTING: 'bg-green-500/10 text-green-500 border-green-500/20',
  SECURITY: 'bg-red-500/10 text-red-500 border-red-500/20',
  DOCUMENTATION: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  CODE_REVIEW: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
}

export function SkillCard({ skill, installed, onInstall, onUninstall }: SkillCardProps) {
  const CategoryIcon = categoryIcons[skill.category] || Code
  const categoryColor = categoryColors[skill.category] || 'bg-gray-500/10 text-gray-500 border-gray-500/20'

  return (
    <Card className="group relative overflow-hidden p-6 transition-all hover:shadow-lg">
      <Link href={`/skills/${skill.id}`} className="block">
        {/* Header */}
        <div className="mb-4 flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className={cn(
              'flex h-10 w-10 items-center justify-center rounded-lg border',
              categoryColor
            )}>
              <CategoryIcon className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-ink-primary group-hover:text-brand-primary transition-colors">
                {skill.name}
              </h3>
              <p className="mt-1 text-sm text-ink-secondary line-clamp-2">
                {skill.description}
              </p>
            </div>
          </div>
        </div>

        {/* Tags */}
        {skill.tags && skill.tags.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {skill.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {skill.tags.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{skill.tags.length - 3}
              </Badge>
            )}
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-ink-tertiary">
          <div className="flex items-center gap-1">
            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            <span>{skill.avg_rating.toFixed(1)}</span>
            <span className="text-ink-quaternary">({skill.review_count})</span>
          </div>
          <div className="flex items-center gap-1">
            <Download className="h-4 w-4" />
            <span>{skill.installation_count}</span>
          </div>
          <div className="flex items-center gap-1">
            <Zap className="h-4 w-4" />
            <span>{skill.execution_count}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-4 flex items-center justify-between border-t border-border-default pt-4">
          <div className="flex items-center gap-2">
            <Badge className={cn('text-xs', categoryColor)}>
              {skill.category.replace('_', ' ')}
            </Badge>
            {skill.author_name && (
              <span className="text-xs text-ink-tertiary">by {skill.author_name}</span>
            )}
          </div>
          {skill.pricing_model === 'free' && (
            <Badge variant="outline" className="text-xs">
              Free
            </Badge>
          )}
        </div>
      </Link>

      {/* Install/Uninstall Button */}
      <div className="absolute right-4 top-4">
        {installed ? (
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onUninstall?.(skill.id)
            }}
            className="rounded-md bg-status-success/10 px-3 py-1.5 text-xs font-medium text-status-success hover:bg-status-success/20 transition-colors"
          >
            Installed
          </button>
        ) : (
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onInstall?.(skill.id)
            }}
            className="rounded-md bg-brand-primary/10 px-3 py-1.5 text-xs font-medium text-brand-primary hover:bg-brand-primary/20 transition-colors"
          >
            Install
          </button>
        )}
      </div>
    </Card>
  )
}

