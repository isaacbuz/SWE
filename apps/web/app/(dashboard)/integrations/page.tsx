'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface Integration {
  id: string
  name: string
  description: string
  status: 'connected' | 'disconnected' | 'error'
  credentialsConfigured: boolean
  rateLimit?: {
    remaining: number
    limit: number
    resetAt: Date
  }
}

/**
 * Integrations Management Page
 * 
 * Manages external API integrations (GitHub, GSA, etc.)
 * with credential management and health monitoring
 */
export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([
    {
      id: 'github',
      name: 'GitHub',
      description: 'GitHub API integration for issues, PRs, and repositories',
      status: 'connected',
      credentialsConfigured: true,
      rateLimit: {
        remaining: 4500,
        limit: 5000,
        resetAt: new Date(Date.now() + 3600000),
      },
    },
    {
      id: 'gsa',
      name: 'GSA APIs',
      description: 'Government Services Administration APIs',
      status: 'disconnected',
      credentialsConfigured: false,
    },
  ])

  const handleConnect = async (id: string) => {
    // Open credential configuration dialog
    console.log(`Connect ${id}`)
  }

  const handleDisconnect = async (id: string) => {
    // Disconnect integration
    setIntegrations((prev) =>
      prev.map((int) =>
        int.id === id ? { ...int, status: 'disconnected' } : int
      )
    )
  }

  const handleTest = async (id: string) => {
    // Test connection
    console.log(`Test ${id}`)
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-ink-primary">Integrations</h1>
        <p className="text-ink-secondary mt-2">
          Manage external API integrations and credentials
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {integrations.map((integration) => (
          <Card key={integration.id} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-ink-primary">
                  {integration.name}
                </h3>
                <p className="text-sm text-ink-secondary mt-1">
                  {integration.description}
                </p>
              </div>
              {integration.status === 'connected' && (
                <CheckCircle className="h-5 w-5 text-green-500" />
              )}
              {integration.status === 'disconnected' && (
                <XCircle className="h-5 w-5 text-gray-400" />
              )}
              {integration.status === 'error' && (
                <AlertCircle className="h-5 w-5 text-red-500" />
              )}
            </div>

            {integration.rateLimit && (
              <div className="mb-4">
                <div className="flex justify-between text-xs text-ink-tertiary mb-1">
                  <span>Rate Limit</span>
                  <span>
                    {integration.rateLimit.remaining} /{' '}
                    {integration.rateLimit.limit}
                  </span>
                </div>
                <div className="w-full bg-surface-tertiary rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{
                      width: `${
                        (integration.rateLimit.remaining /
                          integration.rateLimit.limit) *
                        100
                      }%`,
                    }}
                  />
                </div>
              </div>
            )}

            <div className="flex gap-2">
              {integration.status === 'disconnected' ? (
                <Button
                  onClick={() => handleConnect(integration.id)}
                  className="flex-1"
                >
                  Connect
                </Button>
              ) : (
                <>
                  <Button
                    variant="outline"
                    onClick={() => handleTest(integration.id)}
                    className="flex-1"
                  >
                    Test
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleDisconnect(integration.id)}
                    className="flex-1"
                  >
                    Disconnect
                  </Button>
                </>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
