'use client'

import { useEffect, useState, useCallback } from 'react'
import { useCommand } from '@/components/command/command-provider'
import { ToolSpec } from '@/lib/api/types'
import { listTools } from '@/lib/api/tools'
import { useToolExecutionContext } from '@/components/tools/ToolExecutionProvider'
import { Wrench, GitBranch, Code, Play } from 'lucide-react'

/**
 * Hook to load and register OpenAPI tools in command palette
 */
export function useOpenAPITools() {
  const { registerAction, unregisterAction } = useCommand()
  const { openDialog } = useToolExecutionContext()
  const [tools, setTools] = useState<ToolSpec[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTools()
  }, [])

  useEffect(() => {
    // Register tools as command actions
    tools.forEach((tool) => {
      registerAction({
        id: `tool:${tool.name}`,
        label: tool.name,
        description: tool.description,
        icon: getToolIcon(tool),
        category: 'tools',
        keywords: tool.tags || [],
        onExecute: async () => {
          // Open tool execution dialog
          openDialog(tool)
        },
      })
    })

    // Cleanup on unmount
    return () => {
      tools.forEach((tool) => {
        unregisterAction(`tool:${tool.name}`)
      })
    }
  }, [tools, registerAction, unregisterAction])

  const loadTools = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await listTools()
      setTools(response.tools)
    } catch (err) {
      console.error('Failed to load tools:', err)
      setError(err instanceof Error ? err.message : 'Failed to load tools')
      setTools([]) // Fallback to empty array
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    tools,
    loading,
    error,
    reload: loadTools,
  }
}

function getToolIcon(tool: ToolSpec) {
  if (tool.tags?.includes('github')) {
    return <GitBranch className="h-4 w-4" />
  }
  if (tool.tags?.includes('code')) {
    return <Code className="h-4 w-4" />
  }
  if (tool.tags?.includes('cicd')) {
    return <Play className="h-4 w-4" />
  }
  return <Wrench className="h-4 w-4" />
}

