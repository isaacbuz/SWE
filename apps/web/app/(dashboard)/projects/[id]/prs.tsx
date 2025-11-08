'use client'

import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { mockPRs } from '@/lib/api/mock-data'
import { GitPullRequest } from 'lucide-react'

interface PRsViewProps {
  projectId: string
}

export default function PRsView({ projectId }: PRsViewProps) {
  const prs = mockPRs.filter((pr) => pr.projectId === projectId)

  const statusColors = {
    open: 'success',
    merged: 'info',
    closed: 'secondary',
  } as const

  return (
    <div className="space-y-4">
      {prs.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No pull requests found for this project
        </div>
      ) : (
        prs.map((pr) => (
          <Card key={pr.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <GitPullRequest className="w-5 h-5 mt-1 text-muted-foreground" />
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      #{pr.number} {pr.title}
                    </CardTitle>
                    <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
                      <span>by {pr.author}</span>
                      <span>•</span>
                      <span>{new Date(pr.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <Badge variant={statusColors[pr.status]}>
                  {pr.status}
                </Badge>
              </div>
            </CardHeader>
          </Card>
        ))
      )}
    </div>
  )
}
