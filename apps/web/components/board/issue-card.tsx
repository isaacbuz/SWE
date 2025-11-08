'use client'

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { GripVertical } from 'lucide-react'
import { cn } from '@/lib/utils'

interface IssueCardProps {
  id: string
  title: string
  number: number
  assignee?: string
  priority?: 'high' | 'medium' | 'low'
  labels?: string[]
  className?: string
}

export function IssueCard({
  id,
  title,
  number,
  assignee,
  priority,
  labels,
  className,
}: IssueCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const priorityColors = {
    high: 'destructive',
    medium: 'warning',
    low: 'secondary',
  } as const

  return (
    <Card
      ref={setNodeRef}
      style={style}
      className={cn(
        'cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow',
        isDragging && 'opacity-50',
        className
      )}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-2">
          <button
            className="mt-1 text-muted-foreground hover:text-foreground"
            {...attributes}
            {...listeners}
          >
            <GripVertical className="w-4 h-4" />
          </button>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h4 className="font-medium text-sm leading-tight">
                #{number} {title}
              </h4>
              {priority && (
                <Badge variant={priorityColors[priority]} className="shrink-0 text-xs">
                  {priority}
                </Badge>
              )}
            </div>
            {(assignee || labels) && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {assignee && <span>{assignee}</span>}
                {labels && labels.length > 0 && (
                  <div className="flex gap-1">
                    {labels.map((label) => (
                      <Badge key={label} variant="outline" className="text-xs">
                        {label}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
