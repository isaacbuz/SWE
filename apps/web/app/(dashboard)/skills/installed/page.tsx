'use client'

import { Search, Trash2, Zap, Clock } from 'lucide-react'
import Link from 'next/link'
import { useInstalledSkills, useUninstallSkill } from '@/lib/hooks/use-skills'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useState } from 'react'

export default function InstalledSkillsPage() {
  const [search, setSearch] = useState('')
  const { data: installedSkills, isLoading } = useInstalledSkills()
  const uninstallSkill = useUninstallSkill()

  const filteredSkills = installedSkills?.filter((skill) =>
    skill.skill_id.toLowerCase().includes(search.toLowerCase())
  )

  const handleUninstall = (skillId: string) => {
    if (confirm('Are you sure you want to uninstall this skill?')) {
      uninstallSkill.mutate(skillId)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-ink-primary">Installed Skills</h1>
        <p className="mt-2 text-ink-secondary">
          Manage your installed Skills and view usage statistics
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-tertiary" />
        <Input
          type="text"
          placeholder="Search installed skills..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Skills List */}
      {isLoading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-surface-secondary" />
          ))}
        </div>
      )}

      {!isLoading && installedSkills && (
        <>
          {filteredSkills && filteredSkills.length === 0 ? (
            <Card className="p-12 text-center">
              {installedSkills.length === 0 ? (
                <>
                  <p className="text-ink-secondary">You haven&apos;t installed any skills yet.</p>
                  <Link href="/skills">
                    <Button className="mt-4">Browse Marketplace</Button>
                  </Link>
                </>
              ) : (
                <p className="text-ink-secondary">No skills match your search.</p>
              )}
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredSkills?.map((installation) => (
                <Card key={installation.id} className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <Link
                          href={`/skills/${installation.skill_id}`}
                          className="text-lg font-semibold text-ink-primary hover:text-brand-primary transition-colors"
                        >
                          Skill {installation.skill_id.slice(0, 8)}...
                        </Link>
                        <Badge variant="outline">{installation.version}</Badge>
                        {installation.enabled ? (
                          <Badge className="bg-status-success/10 text-status-success border-status-success/20">
                            Enabled
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Disabled</Badge>
                        )}
                      </div>

                      <div className="mt-3 flex items-center gap-4 text-sm text-ink-tertiary">
                        <div className="flex items-center gap-1">
                          <Zap className="h-4 w-4" />
                          <span>{installation.use_count} uses</span>
                        </div>
                        {installation.last_used_at && (
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            <span>
                              Last used {new Date(installation.last_used_at).toLocaleDateString()}
                            </span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <span>
                            Installed {new Date(installation.installed_at).toLocaleDateString()}
                          </span>
                        </div>
                        {installation.auto_update && (
                          <Badge variant="outline" className="text-xs">
                            Auto-update
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Link href={`/skills/${installation.skill_id}`}>
                        <Button variant="outline" size="sm">
                          View Details
                        </Button>
                      </Link>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUninstall(installation.skill_id)}
                        disabled={uninstallSkill.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

