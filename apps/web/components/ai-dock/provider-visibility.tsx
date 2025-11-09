'use client'

import React, { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, RefreshCw, CheckCircle2, XCircle, Clock, DollarSign, Zap } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface Provider {
  id: string
  name: string
  model: string
  status: 'healthy' | 'degraded' | 'down'
  latency?: number
  costPer1kTokens?: number
}

interface ToolCall {
  id: string
  name: string
  duration: number
  status: 'success' | 'failed'
  input?: Record<string, any>
  output?: Record<string, any>
}

interface Execution {
  id: string
  provider: Provider
  task: string
  duration: number
  toolCalls: ToolCall[]
  tokensIn: number
  tokensOut: number
  cost: number
  timestamp: Date
}

interface ProviderVisibilityProps {
  currentProvider?: Provider
  lastExecution?: Execution
  onProviderSwitch?: (providerId: string) => void
  onRerun?: (providerId: string) => void
}

export function ProviderVisibility({
  currentProvider,
  lastExecution,
  onProviderSwitch,
  onRerun,
}: ProviderVisibilityProps) {
  const [expandedTool, setExpandedTool] = useState<string | null>(null)
  const [showProviderSelector, setShowProviderSelector] = useState(false)
  const [providers, setProviders] = useState<Provider[]>([])

  useEffect(() => {
    // Load available providers
    async function loadProviders() {
      try {
        const response = await fetch('/api/v1/providers')
        if (response.ok) {
          const data = await response.json()
          setProviders(data.providers || [])
        } else {
          // Fallback to static providers
          setProviders([
            { id: 'openai:gpt-4', name: 'OpenAI', model: 'GPT-4', status: 'healthy', latency: 1200, costPer1kTokens: 0.03 },
            { id: 'openai:gpt-4-turbo', name: 'OpenAI', model: 'GPT-4 Turbo', status: 'healthy', latency: 800, costPer1kTokens: 0.01 },
            { id: 'anthropic:claude-opus', name: 'Anthropic', model: 'Claude Opus', status: 'healthy', latency: 1500, costPer1kTokens: 0.075 },
            { id: 'anthropic:claude-sonnet', name: 'Anthropic', model: 'Claude Sonnet', status: 'healthy', latency: 1000, costPer1kTokens: 0.015 },
            { id: 'anthropic:claude-haiku', name: 'Anthropic', model: 'Claude Haiku', status: 'degraded', latency: 600, costPer1kTokens: 0.005 },
          ])
        }
      } catch (error) {
        console.error('Failed to load providers:', error)
      }
    }
    loadProviders()
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'degraded':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'down':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'down':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-4">
      {/* Current Provider */}
      <div className="rounded-lg border border-border-subtle bg-surface-secondary p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-brand-primary" />
            <span className="text-sm font-medium text-ink-primary">AI Provider</span>
          </div>
          {currentProvider && (
            <div className={cn("h-2 w-2 rounded-full", getStatusColor(currentProvider.status))} />
          )}
        </div>

        {currentProvider ? (
          <>
            <div className="mb-3">
              <div className="text-sm font-semibold text-ink-primary">
                {currentProvider.name} {currentProvider.model}
              </div>
              <div className="text-xs text-ink-tertiary">
                Status: {currentProvider.status === 'healthy' ? '🟢 Healthy' : currentProvider.status === 'degraded' ? '🟡 Degraded' : '🔴 Down'}
              </div>
            </div>

            <button
              onClick={() => setShowProviderSelector(!showProviderSelector)}
              className="w-full flex items-center justify-between px-3 py-2 text-sm border border-border-subtle rounded-md hover:bg-surface-tertiary"
            >
              <span>Switch Provider</span>
              {showProviderSelector ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showProviderSelector && (
              <div className="mt-2 border border-border-subtle rounded-md bg-white">
                {providers.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => {
                      onProviderSwitch?.(provider.id)
                      setShowProviderSelector(false)
                    }}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-surface-secondary",
                      currentProvider.id === provider.id && "bg-blue-50"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {getStatusIcon(provider.status)}
                      <span>{provider.name} {provider.model}</span>
                    </div>
                    {currentProvider.id === provider.id && (
                      <span className="text-xs text-blue-600">Current</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="text-sm text-ink-tertiary">No provider selected</div>
        )}
      </div>

      {/* Last Execution */}
      {lastExecution && (
        <div className="rounded-lg border border-border-subtle bg-surface-secondary p-4">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="h-4 w-4 text-brand-primary" />
            <span className="text-sm font-medium text-ink-primary">Last Execution</span>
          </div>

          <div className="space-y-2 mb-4">
            <div className="text-sm">
              <span className="text-ink-tertiary">Task: </span>
              <span className="text-ink-primary font-medium">{lastExecution.task}</span>
            </div>
            <div className="text-sm">
              <span className="text-ink-tertiary">Duration: </span>
              <span className="text-ink-primary font-medium">{(lastExecution.duration / 1000).toFixed(1)}s</span>
            </div>
          </div>

          {/* Tool Calls */}
          {lastExecution.toolCalls.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-medium text-ink-secondary mb-2">
                Tool Calls ({lastExecution.toolCalls.length}):
              </div>
              <div className="space-y-2">
                {lastExecution.toolCalls.map((toolCall) => (
                  <div
                    key={toolCall.id}
                    className="border border-border-subtle rounded-md p-2 bg-white"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        {toolCall.status === 'success' ? (
                          <CheckCircle2 className="h-3 w-3 text-green-500" />
                        ) : (
                          <XCircle className="h-3 w-3 text-red-500" />
                        )}
                        <span className="text-xs font-medium text-ink-primary">{toolCall.name}</span>
                      </div>
                      <button
                        onClick={() => setExpandedTool(expandedTool === toolCall.id ? null : toolCall.id)}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        {expandedTool === toolCall.id ? 'Hide' : 'View'} Details
                      </button>
                    </div>
                    <div className="text-xs text-ink-tertiary">
                      Duration: {(toolCall.duration / 1000).toFixed(1)}s
                    </div>

                    {expandedTool === toolCall.id && (
                      <div className="mt-2 pt-2 border-t border-border-subtle space-y-2">
                        {toolCall.input && (
                          <div>
                            <div className="text-xs font-medium text-ink-secondary mb-1">Input:</div>
                            <pre className="text-xs bg-surface-tertiary p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(toolCall.input, null, 2)}
                            </pre>
                          </div>
                        )}
                        {toolCall.output && (
                          <div>
                            <div className="text-xs font-medium text-ink-secondary mb-1">Output:</div>
                            <pre className="text-xs bg-surface-tertiary p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(toolCall.output, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cost Analysis */}
          <div className="border-t border-border-subtle pt-3">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="h-4 w-4 text-brand-primary" />
              <span className="text-sm font-medium text-ink-primary">Cost Analysis</span>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-ink-tertiary">Tokens:</span>
                <span className="text-ink-primary">
                  {lastExecution.tokensIn.toLocaleString()} in / {lastExecution.tokensOut.toLocaleString()} out
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-tertiary">Cost:</span>
                <span className="text-ink-primary font-medium">${lastExecution.cost.toFixed(4)}</span>
              </div>
            </div>

            {providers.length > 1 && (
              <button
                onClick={() => {
                  // Find alternative provider
                  const alternative = providers.find(p => p.id !== lastExecution.provider.id)
                  if (alternative) {
                    onRerun?.(alternative.id)
                  }
                }}
                className="mt-3 w-full px-3 py-2 text-xs border border-border-subtle rounded-md hover:bg-surface-tertiary flex items-center justify-center gap-2"
              >
                <RefreshCw className="h-3 w-3" />
                Re-run with different provider
              </button>
            )}
          </div>
        </div>
      )}

      {/* Session Stats */}
      <div className="rounded-lg border border-border-subtle bg-surface-secondary p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="h-4 w-4 text-brand-primary" />
          <span className="text-sm font-medium text-ink-primary">Session Stats</span>
        </div>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-ink-tertiary">Total Requests:</span>
            <span className="text-ink-primary">12</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink-tertiary">Total Cost:</span>
            <span className="text-ink-primary">$0.34</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink-tertiary">Avg Latency:</span>
            <span className="text-ink-primary">2.1s</span>
          </div>
        </div>
      </div>
    </div>
  )
}

