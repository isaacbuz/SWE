'use client'

import React from 'react'
import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface SuggestionChipProps {
  label: string
  onClick: () => void
  variant?: 'default' | 'primary'
}

export function SuggestionChip({ 
  label, 
  onClick, 
  variant = 'default' 
}: SuggestionChipProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "group flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition-all",
        "hover:shadow-e2",
        variant === 'default' && "border-border-subtle bg-surface-secondary hover:border-brand-primary hover:bg-surface-primary",
        variant === 'primary' && "border-brand-primary bg-brand-primary/5 hover:bg-brand-primary/10"
      )}
    >
      <Sparkles className={cn(
        "h-4 w-4 transition-colors",
        variant === 'default' && "text-ink-tertiary group-hover:text-brand-primary",
        variant === 'primary' && "text-brand-primary"
      )} />
      <span className="text-ink-primary">{label}</span>
    </button>
  )
}
