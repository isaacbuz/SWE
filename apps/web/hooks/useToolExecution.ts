'use client'

import { useState, useCallback } from 'react'
import { executeTool, ToolExecuteRequest, ToolExecuteResponse } from '@/lib/api/tools'

interface ToolExecutionState {
  executing: boolean
  result: ToolExecuteResponse | null
  error: string | null
  executionHistory: ToolExecuteResponse[]
}

/**
 * Hook for tool execution with state management
 */
export function useToolExecution() {
  const [state, setState] = useState<ToolExecutionState>({
    executing: false,
    result: null,
    error: null,
    executionHistory: [],
  })

  const execute = useCallback(async (request: ToolExecuteRequest) => {
    setState((prev) => ({
      ...prev,
      executing: true,
      error: null,
    }))

    try {
      const result = await executeTool(request)
      
      setState((prev) => ({
        executing: false,
        result,
        error: null,
        executionHistory: [result, ...prev.executionHistory].slice(0, 50), // Keep last 50
      }))

      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Tool execution failed'
      
      setState((prev) => ({
        ...prev,
        executing: false,
        error: errorMessage,
      }))

      throw err
    }
  }, [])

  const clearResult = useCallback(() => {
    setState((prev) => ({
      ...prev,
      result: null,
      error: null,
    }))
  }, [])

  return {
    ...state,
    execute,
    clearResult,
  }
}

