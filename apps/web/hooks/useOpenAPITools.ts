'use client'

import { useEffect, useState } from 'react'
import { useCommand } from '@/components/command/command-provider'
import { ToolSpec } from '@ai-company/openapi-tools'
import { Wrench, GitBranch, Code, Play } from 'lucide-react'

/**
 * Hook to load and register OpenAPI tools in command palette
 */
export function useOpenAPITools() {
  const { registerAction, unregisterAction } = useCommand()
  const [tools, setTools] = useState<ToolSpec[]>([])
  const [loading, setLoading] = useState(true)

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
        category: 'actions',
        keywords: tool.tags || [],
        onExecute: async () => {
          // Open tool execution dialog
          // This would trigger a modal/dialog for parameter input
          console.log(`Execute tool: ${tool.name}`)
          // In real implementation, would open ToolExecutionDialog
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

  async function loadTools() {
    try {
      // In real implementation, would fetch from API
      // const response = await fetch('/api/v1/tools')
      // const data = await response.json()
      // setTools(data.tools)
      
      // For now, mock data
      setTools([])
    } catch (error) {
      console.error('Failed to load tools:', error)
    } finally {
      setLoading(false)
    }
  }

  return { tools, loading }
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

