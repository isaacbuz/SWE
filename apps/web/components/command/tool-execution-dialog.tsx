'use client'

import React, { useState } from 'react'
import { ToolSpec, ToolExecutionRequest, ToolExecutionResult } from '@/lib/api/tools'
import { useExecuteTool } from '@/lib/hooks/use-tools'
import { ToolParameterForm } from './tool-parameter-form'
import { X, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface ToolExecutionDialogProps {
  tool: ToolSpec | null
  onClose: () => void
}

export function ToolExecutionDialog({ tool, onClose }: ToolExecutionDialogProps) {
  const [executionResult, setExecutionResult] = useState<ToolExecutionResult | null>(null)
  const executeTool = useExecuteTool()

  const handleExecute = async (request: ToolExecutionRequest) => {
    try {
      const result = await executeTool.mutateAsync(request)
      setExecutionResult(result)
    } catch (error: any) {
      setExecutionResult({
        success: false,
        error: error.message || 'Tool execution failed',
        executionTimeMs: 0,
      })
    }
  }

  if (!tool) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-xl border border-border-default bg-white shadow-e4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-border-subtle bg-white px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">Execute Tool: {tool.name}</h2>
            <p className="text-sm text-ink-tertiary">{tool.description}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-ink-tertiary hover:text-ink-primary transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          {!executionResult ? (
            <ToolParameterForm
              tool={tool}
              onExecute={handleExecute}
              onCancel={onClose}
            />
          ) : (
            <div className="space-y-4">
              <div
                className={cn(
                  'flex items-center gap-3 rounded-lg p-4',
                  executionResult.success
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-red-50 border border-red-200'
                )}
              >
                {executionResult.success ? (
                  <CheckCircle2 className="h-6 w-6 text-green-600" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-600" />
                )}
                <div className="flex-1">
                  <h3
                    className={cn(
                      'font-semibold',
                      executionResult.success ? 'text-green-900' : 'text-red-900'
                    )}
                  >
                    {executionResult.success ? 'Execution Successful' : 'Execution Failed'}
                  </h3>
                  {executionResult.error && (
                    <p className="text-sm text-red-700 mt-1">{executionResult.error}</p>
                  )}
                  <p className="text-xs text-gray-600 mt-1">
                    Execution time: {executionResult.executionTimeMs}ms
                  </p>
                </div>
              </div>

              {executionResult.success && executionResult.result && (
                <div className="space-y-2">
                  <h4 className="font-medium">Result:</h4>
                  <pre className="bg-gray-50 rounded-lg p-4 text-sm overflow-x-auto">
                    {JSON.stringify(executionResult.result, null, 2)}
                  </pre>
                </div>
              )}

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setExecutionResult(null)
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Run Again
                </button>
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

