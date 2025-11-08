'use client'

import { useEffect } from 'react'
import { useCommand } from '@/components/command/command-provider'
import { FileText, GitPullRequest, Settings, Home } from 'lucide-react'

export default function HomePage() {
  const { registerAction } = useCommand()

  // Register command actions
  useEffect(() => {
    registerAction({
      id: 'new-spec',
      label: '/spec new - Create new specification',
      description: 'Create a new specification document',
      icon: <FileText className="h-4 w-4" />,
      shortcut: '⌘N',
      category: 'actions',
      onExecute: () => {
        console.log('Creating new spec...')
        alert('Creating new specification!')
      },
      keywords: ['spec', 'create', 'new', 'document'],
    })

    registerAction({
      id: 'review-pr',
      label: '/review - Start code review',
      description: 'Start an AI-powered code review',
      icon: <GitPullRequest className="h-4 w-4" />,
      shortcut: '⌘R',
      category: 'actions',
      onExecute: () => {
        console.log('Starting review...')
        alert('Starting code review!')
      },
      keywords: ['review', 'code', 'pr', 'pull request'],
    })

    registerAction({
      id: 'nav-home',
      label: 'Home',
      description: 'Go to home page',
      icon: <Home className="h-4 w-4" />,
      category: 'navigate',
      onExecute: () => {
        console.log('Navigate to home')
      },
      keywords: ['home', 'dashboard'],
    })

    registerAction({
      id: 'nav-settings',
      label: 'Settings',
      description: 'Open settings',
      icon: <Settings className="h-4 w-4" />,
      category: 'navigate',
      onExecute: () => {
        console.log('Navigate to settings')
      },
      keywords: ['settings', 'preferences', 'config'],
    })
  }, [registerAction])

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-ink-primary">
            Welcome to AI Agent Company
          </h1>
          <p className="mt-2 text-lg text-ink-secondary">
            Premium AI-Native Development Platform
          </p>
        </header>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <DemoCard
            title="Command Palette"
            description="Press ⌘K to open the universal command palette"
            shortcut="⌘K"
          />
          <DemoCard
            title="AI Dock"
            description="Toggle the AI copilot dock with ⌘/"
            shortcut="⌘/"
          />
          <DemoCard
            title="Slash Commands"
            description="Try /spec new, /review, /deploy, /diagram"
            shortcut="/"
          />
        </div>

        <div className="mt-12 rounded-xl border border-border-subtle bg-surface-secondary p-6">
          <h2 className="mb-4 text-2xl font-semibold text-ink-primary">
            Features Implemented
          </h2>
          <ul className="space-y-3">
            <FeatureItem
              title="Universal Command Palette"
              description="Fuzzy search, grouped results, keyboard navigation, recent items"
            />
            <FeatureItem
              title="AI Dock with Context Awareness"
              description="Executive summaries, risk indicators, contextual suggestions, real-time updates"
            />
            <FeatureItem
              title="Slash Commands System"
              description="/spec new, /review, /deploy, /diagram with extensible registry"
            />
            <FeatureItem
              title="WebSocket Integration"
              description="Real-time updates for AI suggestions and project events"
            />
            <FeatureItem
              title="Keyboard Shortcuts"
              description="⌘K (Command Palette), ⌘/ (AI Dock), ⌘B (Left Rail)"
            />
            <FeatureItem
              title="State Management"
              description="Zustand for UI state, TanStack Query for server state"
            />
          </ul>
        </div>
      </div>
    </div>
  )
}

function DemoCard({
  title,
  description,
  shortcut,
}: {
  title: string
  description: string
  shortcut: string
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-white p-6 shadow-e1 transition-shadow hover:shadow-e2">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-ink-primary">{title}</h3>
        <kbd className="rounded border border-border-subtle bg-surface-tertiary px-2 py-1 font-mono text-sm text-ink-secondary">
          {shortcut}
        </kbd>
      </div>
      <p className="text-sm text-ink-secondary">{description}</p>
    </div>
  )
}

function FeatureItem({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <li className="flex items-start gap-3">
      <div className="mt-1 h-2 w-2 rounded-full bg-brand-primary" />
      <div>
        <h4 className="font-medium text-ink-primary">{title}</h4>
        <p className="text-sm text-ink-tertiary">{description}</p>
      </div>
    </li>
  )
}
