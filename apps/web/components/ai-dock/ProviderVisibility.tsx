'use client'

import React from 'react'
import { Zap, Clock, DollarSign } from 'lucide-react'

interface ProviderVisibilityProps {
  providerName?: string
  toolCalls?: Array<{
    tool: string
    args: unknown
    result?: unknown
    durationMs: number
  }>
  cost?: number
  tokensUsed?: {
    input: number
    output: number
  }
}

/**
 * Provider visibility component for AI Dock
 * Shows current provider, tool calls, and usage metrics
 */
export function ProviderVisibility({
  providerName,
  toolCalls,
  cost,
  tokensUsed,
}: ProviderVisibilityProps) {
  return (
    <div className="space-y-4">
      {providerName && (
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-ink-secondary" />
          <span className="text-sm font-medium text-ink-primary">
            Provider: {providerName}
          </span>
        </div>
      )}

      {cost !== undefined && (
        <div className="flex items-center gap-2">
          <DollarSign className="h-4 w-4 text-ink-secondary" />
          <span className="text-sm text-ink-secondary">
            Cost: ${cost.toFixed(4)}
          </span>
        </div>
      )}

      {tokensUsed && (
        <div className="text-xs text-ink-tertiary">
          Tokens: {tokensUsed.input} in / {tokensUsed.output} out
        </div>
      )}

      {toolCalls && toolCalls.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-medium text-ink-primary">
            Tool Calls ({toolCalls.length})
          </div>
          <div className="space-y-1">
            {toolCalls.map((call, index) => (
              <div
                key={index}
                className="text-xs bg-surface-secondary rounded px-2 py-1"
              >
                <div className="font-mono text-ink-primary">{call.tool}</div>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="h-3 w-3 text-ink-tertiary" />
                  <span className="text-ink-tertiary">
                    {call.durationMs}ms
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

