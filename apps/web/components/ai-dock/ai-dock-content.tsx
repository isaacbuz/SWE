'use client'

import React, { useState } from 'react'
import { X, Settings, Sparkles } from 'lucide-react'
import { useUIStore } from '@/lib/stores/ui-store'
import { cn } from '@/lib/utils/cn'
import { SuggestionChip } from './suggestion-chip'
import { PromptBar } from './prompt-bar'
import { ExecSummary } from './exec-summary'
import { RiskList } from './risk-list'
import { ProviderVisibility, ProviderInfo, ExecutionMetrics } from './provider-visibility'

type TabType = 'summary' | 'risks' | 'actions' | 'provider'

interface AIDockContentProps {
  context?: {
    projectId?: string
    projectName?: string
    route?: string
  }
}

export function AIDockContent({ context }: AIDockContentProps) {
  const { aiDockCollapsed, toggleAIDock } = useUIStore()
  const [activeTab, setActiveTab] = useState<TabType>('summary')

  if (aiDockCollapsed) {
    return (
      <div className="fixed right-0 top-0 h-full w-12 border-l border-border-subtle bg-surface-primary">
        <button
          onClick={toggleAIDock}
          className="flex h-12 w-full items-center justify-center hover:bg-surface-secondary"
          aria-label="Expand AI Dock"
        >
          <Sparkles className="h-5 w-5 text-brand-primary" />
        </button>
      </div>
    )
  }

  return (
    <div className="fixed right-0 top-0 flex h-full w-[360px] flex-col border-l border-border-subtle bg-surface-primary">
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b border-border-subtle px-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-brand-primary" />
          <h2 className="text-sm font-semibold text-ink-primary">
            {context?.projectName || 'AI Copilot'}
          </h2>
        </div>
        <div className="flex items-center gap-1">
          <button
            className="rounded p-1 hover:bg-surface-secondary"
            aria-label="Settings"
          >
            <Settings className="h-4 w-4 text-ink-tertiary" />
          </button>
          <button
            onClick={toggleAIDock}
            className="rounded p-1 hover:bg-surface-secondary"
            aria-label="Close"
          >
            <X className="h-4 w-4 text-ink-tertiary" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border-subtle">
        <Tab
          active={activeTab === 'summary'}
          onClick={() => setActiveTab('summary')}
        >
          Exec Summary
        </Tab>
        <Tab
          active={activeTab === 'risks'}
          onClick={() => setActiveTab('risks')}
        >
          Risks
        </Tab>
        <Tab
          active={activeTab === 'actions'}
          onClick={() => setActiveTab('actions')}
        >
          Actions
        </Tab>
        <Tab
          active={activeTab === 'provider'}
          onClick={() => setActiveTab('provider')}
        >
          Provider
        </Tab>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'summary' && <ExecSummary context={context} />}
        {activeTab === 'risks' && <RiskList context={context} />}
        {activeTab === 'actions' && <ActionsSuggestions context={context} />}
        {activeTab === 'provider' && (
          <ProviderTab
            context={context}
            onProviderChange={(providerId) => {
              console.log('Provider changed to:', providerId)
              // TODO: Implement provider change logic
            }}
            onRerun={(providerId) => {
              console.log('Re-run with provider:', providerId)
              // TODO: Implement re-run logic
            }}
          />
        )}
      </div>

      {/* Footer - Prompt Bar */}
      <div className="border-t border-border-subtle p-4">
        <PromptBar />
      </div>
    </div>
  )
}

function Tab({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex-1 border-b-2 px-4 py-2 text-sm font-medium transition-colors',
        active
          ? 'border-brand-primary text-brand-primary'
          : 'border-transparent text-ink-tertiary hover:text-ink-secondary'
      )}
    >
      {children}
    </button>
  )
}

function ActionsSuggestions({ context }: { context?: any }) {
  const suggestions = getContextualSuggestions(context)

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-ink-primary">
        Suggested Actions
      </h3>
      <div className="space-y-2">
        {suggestions.map((suggestion, index) => (
          <SuggestionChip
            key={index}
            label={suggestion.label}
            onClick={suggestion.onClick}
          />
        ))}
      </div>
    </div>
  )
}

function getContextualSuggestions(context?: any) {
  // Context-aware suggestions based on current route
  const route = context?.route || '/'

  if (route.includes('/projects')) {
    return [
      {
        label: 'Summarize recent PRs',
        onClick: () => console.log('Summarize PRs'),
      },
      {
        label: 'Create roadmap',
        onClick: () => console.log('Create roadmap'),
      },
      {
        label: 'Generate test plan',
        onClick: () => console.log('Generate test plan'),
      },
      {
        label: 'Estimate costs',
        onClick: () => console.log('Estimate costs'),
      },
    ]
  }

  if (route.includes('/agents')) {
    return [
      {
        label: 'Compose crew for migration',
        onClick: () => console.log('Compose crew'),
      },
      {
        label: 'Benchmark models',
        onClick: () => console.log('Benchmark models'),
      },
      {
        label: 'Analyze agent performance',
        onClick: () => console.log('Analyze performance'),
      },
    ]
  }

  // Default suggestions
  return [
    {
      label: 'Summarize latest activity',
      onClick: () => console.log('Summarize activity'),
    },
    {
      label: 'Review pending PRs',
      onClick: () => console.log('Review PRs'),
    },
    {
      label: 'Check system health',
      onClick: () => console.log('Check health'),
    },
  ]
}

function ProviderTab({
  context,
  onProviderChange,
  onRerun,
}: {
  context?: any
  onProviderChange: (providerId: string) => void
  onRerun: (providerId?: string) => void
}) {
  // Mock data - in production, this would come from API/hooks
  const mockMetrics: ExecutionMetrics | undefined = {
    provider: {
      id: 'openai',
      name: 'OpenAI',
      model: 'GPT-4 Turbo',
      status: 'active',
      health: 'healthy',
    },
    toolCalls: [
      {
        id: '1',
        toolName: 'analyzeCode',
        arguments: { code: '...', language: 'typescript' },
        result: { issues: 3, suggestions: 5 },
        durationMs: 1200,
        timestamp: new Date(),
      },
      {
        id: '2',
        toolName: 'createIssues',
        arguments: { repository: 'owner/repo', issues: [] },
        result: { created: 5 },
        durationMs: 800,
        timestamp: new Date(),
      },
    ],
    tokensInput: 2450,
    tokensOutput: 1200,
    cost: 0.042,
    totalDurationMs: 2000,
    success: true,
  }

  const mockProviders: ProviderInfo[] = [
    {
      id: 'openai',
      name: 'OpenAI',
      model: 'GPT-4 Turbo',
      status: 'active',
      health: 'healthy',
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      model: 'Claude 3 Opus',
      status: 'idle',
      health: 'healthy',
    },
    {
      id: 'google',
      name: 'Google',
      model: 'Gemini Pro',
      status: 'idle',
      health: 'degraded',
    },
  ]

  return (
    <ProviderVisibility
      metrics={mockMetrics}
      availableProviders={mockProviders}
      onProviderChange={onProviderChange}
      onRerun={onRerun}
    />
  )
}
