'use client'

import { useState } from 'react'
import { Search, Filter, Plus, Grid, List as ListIcon } from 'lucide-react'
import { useSkills, useInstallSkill, useUninstallSkill, useInstalledSkills } from '@/lib/hooks/use-skills'
import { Skill } from '@/lib/api/types'
import { SkillCard } from '@/components/skills/skill-card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Link from 'next/link'

const categories = [
  { value: '', label: 'All Categories' },
  { value: 'CODE_GENERATION', label: 'Code Generation' },
  { value: 'TESTING', label: 'Testing' },
  { value: 'SECURITY', label: 'Security' },
  { value: 'DOCUMENTATION', label: 'Documentation' },
  { value: 'CODE_REVIEW', label: 'Code Review' },
]

const sortOptions = [
  { value: 'updated_at', label: 'Recently Updated' },
  { value: 'created_at', label: 'Newest' },
  { value: 'download_count', label: 'Most Popular' },
  { value: 'avg_rating', label: 'Highest Rated' },
  { value: 'execution_count', label: 'Most Used' },
]

export default function SkillsMarketplacePage() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState('updated_at')
  const [view, setView] = useState<'grid' | 'list'>('grid')

  const { data: skills, isLoading, error } = useSkills({
    search: search || undefined,
    category: category || undefined,
    sort,
    order: 'desc',
    limit: 50,
  })

  const { data: installedSkills } = useInstalledSkills()
  const installedIds = new Set(installedSkills?.map(s => s.skill_id) || [])

  const installSkill = useInstallSkill()
  const uninstallSkill = useUninstallSkill()

  const handleInstall = (skillId: string) => {
    installSkill.mutate({ skillId })
  }

  const handleUninstall = (skillId: string) => {
    uninstallSkill.mutate(skillId)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink-primary">Skills Marketplace</h1>
          <p className="mt-2 text-ink-secondary">
            Discover and install reusable AI Skills for your development workflow
          </p>
        </div>
        <Link href="/skills/create">
          <Button className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create Skill
          </Button>
        </Link>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-tertiary" />
          <Input
            type="text"
            placeholder="Search skills..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full rounded-md border border-border-default bg-surface-secondary px-4 py-2 text-sm text-ink-primary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary sm:w-48"
        >
          {categories.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="w-full rounded-md border border-border-default bg-surface-secondary px-4 py-2 text-sm text-ink-primary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary sm:w-48"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <Button
            variant={view === 'grid' ? 'default' : 'outline'}
            size="icon"
            onClick={() => setView('grid')}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={view === 'list' ? 'default' : 'outline'}
            size="icon"
            onClick={() => setView('list')}
          >
            <ListIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Skills Grid/List */}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 animate-pulse rounded-lg bg-surface-secondary" />
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-status-error/20 bg-status-error/10 p-4 text-status-error">
          Failed to load skills: {error.message}
        </div>
      )}

      {!isLoading && !error && skills && (
        <>
          {skills.length === 0 ? (
            <div className="rounded-lg border border-border-default bg-surface-secondary p-12 text-center">
              <p className="text-ink-secondary">No skills found. Try adjusting your filters.</p>
            </div>
          ) : (
            <div
              className={
                view === 'grid'
                  ? 'grid gap-4 sm:grid-cols-2 lg:grid-cols-3'
                  : 'space-y-4'
              }
            >
              {skills.map((skill) => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                  installed={installedIds.has(skill.id)}
                  onInstall={handleInstall}
                  onUninstall={handleUninstall}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Stats */}
      {skills && skills.length > 0 && (
        <div className="rounded-lg border border-border-default bg-surface-secondary p-4">
          <p className="text-sm text-ink-secondary">
            Showing {skills.length} skill{skills.length !== 1 ? 's' : ''}
            {installedSkills && installedSkills.length > 0 && (
              <> • {installedSkills.length} installed</>
            )}
          </p>
        </div>
      )}
    </div>
  )
}

