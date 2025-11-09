'use client'

import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { SkillVersion } from '@/lib/api/types'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface VersionListProps {
  versions: SkillVersion[]
  currentVersion?: string
}

export function VersionList({ versions, currentVersion }: VersionListProps) {
  if (versions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No version history available.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {versions.map((version) => {
        const isCurrent = version.version === currentVersion
        const isDeprecated = version.status === 'deprecated'
        const isYanked = version.status === 'yanked'

        return (
          <Card key={version.id} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-lg">
                    v{version.version}
                  </span>
                  {isCurrent && (
                    <Badge variant="default" className="bg-green-500/10 text-green-500 border-green-500/20">
                      Current
                    </Badge>
                  )}
                  {isDeprecated && (
                    <Badge variant="destructive">
                      Deprecated
                    </Badge>
                  )}
                  {isYanked && (
                    <Badge variant="destructive">
                      Yanked
                    </Badge>
                  )}
                  {version.breaking_changes && (
                    <Badge variant="outline" className="border-orange-500 text-orange-500">
                      Breaking Changes
                    </Badge>
                  )}
                </div>
              </div>
              <span className="text-sm text-muted-foreground">
                {new Date(version.created_at).toLocaleDateString()}
              </span>
            </div>

            {version.changelog && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-2">Changelog</h4>
                <div
                  className="prose prose-sm max-w-none text-muted-foreground"
                  dangerouslySetInnerHTML={{ __html: version.changelog }}
                />
              </div>
            )}

            {version.migration_guide && (
              <div className="mt-4 p-4 bg-muted rounded-md">
                <div className="flex items-start gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5" />
                  <h4 className="text-sm font-semibold">Migration Guide</h4>
                </div>
                <div
                  className="prose prose-sm max-w-none text-muted-foreground"
                  dangerouslySetInnerHTML={{ __html: version.migration_guide }}
                />
              </div>
            )}
          </Card>
        )
      })}
    </div>
  )
}

