'use client'

import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

interface KanbanColumnProps {
  id: string
  title: string
  count?: number
  children: React.ReactNode
  items: string[]
  className?: string
}

export function KanbanColumn({
  id,
  title,
  count,
  children,
  items,
  className,
}: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col bg-surface-secondary rounded-lg p-4 min-w-[280px] max-w-[320px]',
        isOver && 'bg-surface-tertiary ring-2 ring-primary',
        className
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm text-ink-primary">{title}</h3>
        {count !== undefined && (
          <Badge variant="secondary" className="ml-2">
            {count}
          </Badge>
        )}
      </div>
      <SortableContext items={items} strategy={verticalListSortingStrategy}>
        <div className="space-y-2 flex-1 overflow-y-auto">
          {children}
        </div>
      </SortableContext>
    </div>
  )
}
