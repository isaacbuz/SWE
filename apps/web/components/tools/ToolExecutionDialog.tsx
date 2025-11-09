'use client'

import React, { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ToolSpec } from '@ai-company/openapi-tools'

interface ToolExecutionDialogProps {
  tool: ToolSpec | null
  open: boolean
  onClose: () => void
  onExecute: (args: unknown) => Promise<void>
}

/**
 * Dialog for executing tools with parameter input
 */
export function ToolExecutionDialog({
  tool,
  open,
  onClose,
  onExecute,
}: ToolExecutionDialogProps) {
  const [args, setArgs] = useState<Record<string, unknown>>({})
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!tool) return null

  const schema = tool.jsonSchema as {
    type?: string
    properties?: Record<string, any>
    required?: string[]
  }

  const properties = schema.properties || {}
  const required = schema.required || []

  const handleSubmit = async () => {
    setError(null)
    setExecuting(true)

    try {
      // Validate required fields
      for (const field of required) {
        if (!args[field]) {
          throw new Error(`Field ${field} is required`)
        }
      }

      await onExecute(args)
      onClose()
      setArgs({})
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed')
    } finally {
      setExecuting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Execute {tool.name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <p className="text-sm text-ink-secondary">{tool.description}</p>

          <div className="space-y-3">
            {Object.entries(properties).map(([key, prop]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-ink-primary mb-1">
                  {key}
                  {required.includes(key) && (
                    <span className="text-red-500 ml-1">*</span>
                  )}
                </label>
                {prop.type === 'string' && (
                  <input
                    type="text"
                    value={(args[key] as string) || ''}
                    onChange={(e) =>
                      setArgs({ ...args, [key]: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-border-default rounded-lg"
                    placeholder={prop.description || key}
                  />
                )}
                {prop.type === 'number' && (
                  <input
                    type="number"
                    value={(args[key] as number) || ''}
                    onChange={(e) =>
                      setArgs({ ...args, [key]: Number(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-border-default rounded-lg"
                  />
                )}
                {prop.type === 'boolean' && (
                  <input
                    type="checkbox"
                    checked={(args[key] as boolean) || false}
                    onChange={(e) =>
                      setArgs({ ...args, [key]: e.target.checked })
                    }
                  />
                )}
                {prop.type === 'array' && (
                  <textarea
                    value={JSON.stringify(args[key] || [])}
                    onChange={(e) => {
                      try {
                        setArgs({ ...args, [key]: JSON.parse(e.target.value) })
                      } catch {
                        // Invalid JSON, ignore
                      }
                    }}
                    className="w-full px-3 py-2 border border-border-default rounded-lg font-mono text-sm"
                    placeholder="[]"
                  />
                )}
                {prop.type === 'object' && (
                  <textarea
                    value={JSON.stringify(args[key] || {}, null, 2)}
                    onChange={(e) => {
                      try {
                        setArgs({ ...args, [key]: JSON.parse(e.target.value) })
                      } catch {
                        // Invalid JSON, ignore
                      }
                    }}
                    className="w-full px-3 py-2 border border-border-default rounded-lg font-mono text-sm"
                    placeholder="{}"
                  />
                )}
                {prop.description && (
                  <p className="text-xs text-ink-tertiary mt-1">
                    {prop.description}
                  </p>
                )}
              </div>
            ))}
          </div>

          {error && (
            <div className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={executing}>
              {executing ? 'Executing...' : 'Execute'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

