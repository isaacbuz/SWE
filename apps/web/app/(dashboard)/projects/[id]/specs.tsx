'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { mockSpecs } from '@/lib/api/mock-data'
import { FileText } from 'lucide-react'

interface SpecsViewProps {
  projectId: string
}

export default function SpecsView({ projectId }: SpecsViewProps) {
  const specs = mockSpecs.filter((s) => s.projectId === projectId)

  const statusColors = {
    draft: 'secondary',
    approved: 'success',
    implemented: 'info',
  } as const

  return (
    <div className="space-y-4">
      {specs.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No specifications found for this project
        </div>
      ) : (
        specs.map((spec) => (
          <Card key={spec.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <FileText className="w-5 h-5 mt-1 text-muted-foreground" />
                  <div className="flex-1">
                    <CardTitle className="text-lg">{spec.title}</CardTitle>
                    <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
                      <span>by {spec.author}</span>
                      <span>•</span>
                      <span>{new Date(spec.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <Badge variant={statusColors[spec.status]}>
                  {spec.status}
                </Badge>
              </div>
            </CardHeader>
          </Card>
        ))
      )}
    </div>
  )
}
