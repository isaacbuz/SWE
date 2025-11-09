'use client'

import React, { useState } from 'react'
import { CheckCircle2, XCircle, Clock, RefreshCw, Key, Settings, ToggleLeft, ToggleRight, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface Integration {
  id: string
  name: string
  description: string
  status: 'connected' | 'disconnected' | 'error'
  health: 'healthy' | 'degraded' | 'down'
  rateLimit?: {
    remaining: number
    limit: number
    resetAt?: Date
  }
  credentials?: {
    masked: string
    lastUpdated?: Date
  }
  tools: Array<{
    id: string
    name: string
    enabled: boolean
    description?: string
  }>
  usage?: {
    last7Days: number
    last30Days: number
  }
}

interface IntegrationDetailProps {
  integration: Integration
  onUpdateCredentials?: (id: string, credentials: Record<string, string>) => Promise<void>
  onTestConnection?: (id: string) => Promise<{ success: boolean; message: string }>
  onToggleTool?: (integrationId: string, toolId: string, enabled: boolean) => Promise<void>
}

export function IntegrationDetail({
  integration,
  onUpdateCredentials,
  onTestConnection,
  onToggleTool,
}: IntegrationDetailProps) {
  const [showCredentialForm, setShowCredentialForm] = useState(false)
  const [credentialValue, setCredentialValue] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  const handleTestConnection = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const result = await onTestConnection?.(integration.id) || { success: false, message: 'Not implemented' }
      setTestResult(result)
    } catch (error) {
      setTestResult({ success: false, message: error instanceof Error ? error.message : 'Test failed' })
    } finally {
      setTesting(false)
    }
  }

  const handleUpdateCredentials = async () => {
    if (!credentialValue.trim()) {
      return
    }

    try {
      await onUpdateCredentials?.(integration.id, {
        token: credentialValue,
      })
      setShowCredentialForm(false)
      setCredentialValue('')
      // Show success toast
    } catch (error) {
      // Show error toast
    }
  }

  const getHealthIcon = () => {
    switch (integration.health) {
      case 'healthy':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      case 'down':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getHealthColor = () => {
    switch (integration.health) {
      case 'healthy':
        return 'text-green-500'
      case 'degraded':
        return 'text-yellow-500'
      case 'down':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  return (
    <div className="rounded-lg border border-border-subtle bg-surface-secondary p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {getHealthIcon()}
          <div>
            <h3 className="text-lg font-semibold text-ink-primary">{integration.name}</h3>
            <p className="text-sm text-ink-secondary">{integration.description}</p>
          </div>
        </div>
        <span className={cn("text-sm font-medium", getHealthColor())}>
          {integration.health === 'healthy' ? '🟢' : integration.health === 'degraded' ? '🟡' : '🔴'}
        </span>
      </div>

      {/* Status */}
      <div className="mb-4 p-3 bg-white rounded-md border border-border-subtle">
        <div className="text-sm">
          <span className="text-ink-tertiary">Status: </span>
          <span className="text-ink-primary font-medium capitalize">{integration.status}</span>
        </div>

        {integration.rateLimit && (
          <div className="mt-2">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-ink-tertiary">Rate Limit:</span>
              <span className="text-ink-primary font-medium">
                {integration.rateLimit.remaining.toLocaleString()} / {integration.rateLimit.limit.toLocaleString()} remaining
              </span>
            </div>
            <div className="w-full bg-surface-tertiary rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${(integration.rateLimit.remaining / integration.rateLimit.limit) * 100}%` }}
              />
            </div>
            {integration.rateLimit.resetAt && (
              <div className="text-xs text-ink-tertiary mt-1">
                Resets: {integration.rateLimit.resetAt.toLocaleTimeString()}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Credentials */}
      {integration.status === 'connected' && (
        <div className="mb-4 p-3 bg-white rounded-md border border-border-subtle">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Key className="h-4 w-4 text-ink-tertiary" />
              <span className="text-sm font-medium text-ink-primary">Credentials</span>
            </div>
            {integration.credentials?.lastUpdated && (
              <span className="text-xs text-ink-tertiary">
                Updated {integration.credentials.lastUpdated.toLocaleDateString()}
              </span>
            )}
          </div>

          {!showCredentialForm ? (
            <div className="flex items-center justify-between">
              <code className="text-sm text-ink-secondary font-mono">
                {integration.credentials?.masked || '••••••••••••••••'}
              </code>
              <button
                onClick={() => setShowCredentialForm(true)}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Update
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <input
                type="password"
                placeholder="Enter new token/API key"
                value={credentialValue}
                onChange={(e) => setCredentialValue(e.target.value)}
                className="w-full px-3 py-2 border border-border-subtle rounded-md text-sm"
              />
              <div className="flex items-center gap-2">
                <button
                  onClick={handleUpdateCredentials}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setShowCredentialForm(false)
                    setCredentialValue('')
                  }}
                  className="px-3 py-1 text-sm border border-border-subtle rounded-md hover:bg-surface-tertiary"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <button
            onClick={handleTestConnection}
            disabled={testing}
            className="mt-3 w-full px-3 py-2 text-sm border border-border-subtle rounded-md hover:bg-surface-tertiary flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {testing ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Test Connection
              </>
            )}
          </button>

          {testResult && (
            <div className={cn(
              "mt-2 p-2 rounded-md text-sm",
              testResult.success ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
            )}>
              {testResult.success ? '✓' : '✗'} {testResult.message}
            </div>
          )}
        </div>
      )}

      {/* Available Tools */}
      {integration.tools.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Settings className="h-4 w-4 text-ink-tertiary" />
            <span className="text-sm font-medium text-ink-primary">
              Available Tools ({integration.tools.length}):
            </span>
          </div>
          <div className="space-y-2">
            {integration.tools.map((tool) => (
              <div
                key={tool.id}
                className="flex items-center justify-between p-2 bg-white rounded-md border border-border-subtle"
              >
                <div className="flex-1">
                  <div className="text-sm font-medium text-ink-primary">{tool.name}</div>
                  {tool.description && (
                    <div className="text-xs text-ink-tertiary">{tool.description}</div>
                  )}
                </div>
                <button
                  onClick={() => onToggleTool?.(integration.id, tool.id, !tool.enabled)}
                  className="text-ink-tertiary hover:text-ink-primary"
                >
                  {tool.enabled ? (
                    <ToggleRight className="h-5 w-5 text-green-500" />
                  ) : (
                    <ToggleLeft className="h-5 w-5" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Usage Statistics */}
      {integration.usage && (
        <div className="border-t border-border-subtle pt-4">
          <span className="text-sm font-medium text-ink-primary mb-2 block">Usage Statistics</span>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-ink-tertiary">Last 7 days:</span>
              <span className="text-ink-primary font-medium">{integration.usage.last7Days} calls</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-tertiary">Last 30 days:</span>
              <span className="text-ink-primary font-medium">{integration.usage.last30Days} calls</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

