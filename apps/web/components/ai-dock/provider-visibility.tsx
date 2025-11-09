'use client'

import React, { useState } from 'react'
import { ChevronDown, ChevronUp, RefreshCw, Zap, DollarSign, Clock, CheckCircle2, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export interface ProviderInfo {
  id: string
  name: string
  model?: string
  status: 'active' | 'idle' | 'error'
  health?: 'healthy' | 'degraded' | 'down'
}

export interface ToolCallTrace {
  id: string
  toolName: string
  arguments: Record<string, any>
  result?: any
  error?: string
  durationMs: number
  timestamp: Date
}

export interface ExecutionMetrics {
  provider: ProviderInfo
  toolCalls: ToolCallTrace[]
  tokensInput: number
  tokensOutput: number
  cost: number
  totalDurationMs: number
  success: boolean
}

interface ProviderVisibilityProps {
  metrics?: ExecutionMetrics
  availableProviders?: ProviderInfo[]
  onProviderChange?: (providerId: string) => void
  onRerun?: (providerId?: string) => void
}

export function ProviderVisibility({
  metrics,
  availableProviders = [],
  onProviderChange,
  onRerun,
}: ProviderVisibilityProps) {
  const [expanded, setExpanded] = useState(false)
  const [showProviderSelector, setShowProviderSelector] = useState(false)

  const currentProvider = metrics?.provider || {
    id: 'none',
    name: 'No provider selected',
    status: 'idle' as const,
  }

  const healthColor = {
    healthy: 'text-green-600',
    degraded: 'text-yellow-600',
    down: 'text-red-600',
  }[currentProvider.health || 'healthy']

  return (
    <div className="space-y-3">
      {/* Provider Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={cn('h-2 w-2 rounded-full', {
            'bg-green-500': currentProvider.status === 'active',
            'bg-gray-400': currentProvider.status === 'idle',
            'bg-red-500': currentProvider.status === 'error',
          })} />
          <div>
            <div className="text-sm font-medium text-ink-primary">
              {currentProvider.name}
            </div>
            {currentProvider.model && (
              <div className="text-xs text-ink-tertiary">
                {currentProvider.model}
              </div>
            )}
          </div>
          {currentProvider.health && (
            <span className={cn('text-xs', healthColor)}>
              {currentProvider.health}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {availableProviders.length > 0 && (
            <button
              onClick={() => setShowProviderSelector(!showProviderSelector)}
              className="flex items-center gap-1 rounded px-2 py-1 text-xs text-ink-secondary hover:bg-surface-secondary"
            >
              Switch
              <ChevronDown className="h-3 w-3" />
            </button>
          )}
          {onRerun && (
            <button
              onClick={() => onRerun()}
              className="flex items-center gap-1 rounded px-2 py-1 text-xs text-ink-secondary hover:bg-surface-secondary"
              title="Re-run with current provider"
            >
              <RefreshCw className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Provider Selector Dropdown */}
      {showProviderSelector && availableProviders.length > 0 && (
        <div className="rounded-lg border border-border-subtle bg-surface-primary p-2">
          <div className="text-xs font-medium text-ink-secondary mb-2">Select Provider:</div>
          <div className="space-y-1">
            {availableProviders.map((provider) => (
              <button
                key={provider.id}
                onClick={() => {
                  onProviderChange?.(provider.id)
                  setShowProviderSelector(false)
                }}
                className={cn(
                  'w-full text-left rounded px-2 py-1.5 text-xs hover:bg-surface-secondary',
                  provider.id === currentProvider.id && 'bg-surface-secondary'
                )}
              >
                <div className="flex items-center justify-between">
                  <span>{provider.name}</span>
                  {provider.health && (
                    <span className={cn('text-xs', healthColor)}>
                      {provider.health}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Metrics Summary */}
      {metrics && (
        <div className="space-y-2">
          {/* Tool Calls Summary */}
          {metrics.toolCalls.length > 0 && (
            <div className="rounded-lg border border-border-subtle bg-surface-secondary p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-medium text-ink-primary">
                  Tool Calls ({metrics.toolCalls.length})
                </div>
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs text-ink-tertiary hover:text-ink-secondary"
                >
                  {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>
              </div>

              {expanded && (
                <div className="space-y-2 mt-2">
                  {metrics.toolCalls.map((call, index) => (
                    <div
                      key={call.id}
                      className="rounded border border-border-subtle bg-surface-primary p-2"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          {call.error ? (
                            <XCircle className="h-3 w-3 text-red-500" />
                          ) : (
                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                          )}
                          <span className="text-xs font-medium text-ink-primary">
                            {index + 1}. {call.toolName}
                          </span>
                        </div>
                        <span className="text-xs text-ink-tertiary">
                          {call.durationMs}ms
                        </span>
                      </div>
                      {call.error && (
                        <div className="text-xs text-red-600 mt-1">
                          {call.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {!expanded && metrics.toolCalls.length > 0 && (
                <div className="text-xs text-ink-tertiary">
                  {metrics.toolCalls.slice(0, 3).map((call, i) => (
                    <div key={call.id} className="truncate">
                      {i + 1}. {call.toolName} ({call.durationMs}ms)
                    </div>
                  ))}
                  {metrics.toolCalls.length > 3 && (
                    <div className="text-xs text-ink-tertiary mt-1">
                      +{metrics.toolCalls.length - 3} more
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Token Usage & Cost */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg border border-border-subtle bg-surface-secondary p-2">
              <div className="flex items-center gap-1 mb-1">
                <Zap className="h-3 w-3 text-ink-tertiary" />
                <span className="text-xs font-medium text-ink-primary">Tokens</span>
              </div>
              <div className="text-xs text-ink-secondary">
                {metrics.tokensInput.toLocaleString()} in / {metrics.tokensOutput.toLocaleString()} out
              </div>
            </div>

            <div className="rounded-lg border border-border-subtle bg-surface-secondary p-2">
              <div className="flex items-center gap-1 mb-1">
                <DollarSign className="h-3 w-3 text-ink-tertiary" />
                <span className="text-xs font-medium text-ink-primary">Cost</span>
              </div>
              <div className="text-xs text-ink-secondary">
                ${metrics.cost.toFixed(6)}
              </div>
            </div>
          </div>

          {/* Total Duration */}
          <div className="flex items-center gap-2 text-xs text-ink-tertiary">
            <Clock className="h-3 w-3" />
            <span>Total: {metrics.totalDurationMs}ms</span>
            {metrics.success ? (
              <CheckCircle2 className="h-3 w-3 text-green-500 ml-auto" />
            ) : (
              <XCircle className="h-3 w-3 text-red-500 ml-auto" />
            )}
          </div>

          {/* Re-run with Different Provider */}
          {onRerun && availableProviders.length > 1 && (
            <div className="pt-2 border-t border-border-subtle">
              <div className="text-xs font-medium text-ink-secondary mb-2">
                Re-run with different provider:
              </div>
              <div className="flex flex-wrap gap-1">
                {availableProviders
                  .filter(p => p.id !== currentProvider.id)
                  .slice(0, 3)
                  .map((provider) => (
                    <button
                      key={provider.id}
                      onClick={() => onRerun(provider.id)}
                      className="rounded px-2 py-1 text-xs bg-surface-tertiary hover:bg-surface-secondary text-ink-secondary"
                    >
                      {provider.name}
                    </button>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!metrics && (
        <div className="rounded-lg border border-border-subtle bg-surface-secondary p-4 text-center">
          <div className="text-xs text-ink-tertiary">
            No execution metrics available
          </div>
          <div className="text-xs text-ink-tertiary mt-1">
            Run a tool or AI request to see provider information
          </div>
        </div>
      )}
    </div>
  )
}

