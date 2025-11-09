'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'
import { ToolSpec } from '@/lib/api/types'
import { ToolExecutionDialog } from './ToolExecutionDialog'
import { useToolExecution } from '@/hooks/useToolExecution'

interface ToolExecutionContextValue {
  openDialog: (tool: ToolSpec) => void
  closeDialog: () => void
  executionHistory: ReturnType<typeof useToolExecution>['executionHistory']
}

const ToolExecutionContext = createContext<ToolExecutionContextValue | null>(null)

export function ToolExecutionProvider({ children }: { children: ReactNode }) {
  const [selectedTool, setSelectedTool] = useState<ToolSpec | null>(null)
  const { execute, executionHistory } = useToolExecution()

  const openDialog = (tool: ToolSpec) => {
    setSelectedTool(tool)
  }

  const closeDialog = () => {
    setSelectedTool(null)
  }

  const handleExecute = async (result: any) => {
    // Tool execution handled by dialog
    // This is just for closing the dialog
    closeDialog()
  }

  return (
    <ToolExecutionContext.Provider
      value={{
        openDialog,
        closeDialog,
        executionHistory,
      }}
    >
      {children}
      <ToolExecutionDialog
        tool={selectedTool}
        open={selectedTool !== null}
        onClose={closeDialog}
        onExecute={handleExecute}
      />
    </ToolExecutionContext.Provider>
  )
}

export function useToolExecutionContext() {
  const context = useContext(ToolExecutionContext)
  if (!context) {
    throw new Error('useToolExecutionContext must be used within ToolExecutionProvider')
  }
  return context
}

