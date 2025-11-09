'use client'

import { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CommandProvider } from '@/components/command/command-provider'
import { ToolExecutionProvider } from '@/components/tools/ToolExecutionProvider'
import { WebSocketProvider } from '@/lib/websocket/websocket-provider'
import { useKeyboardShortcuts } from '@/lib/hooks/use-keyboard-shortcuts'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
})

function KeyboardShortcutsHandler() {
  useKeyboardShortcuts()
  return null
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <CommandProvider>
          <ToolExecutionProvider>
            <KeyboardShortcutsHandler />
            {children}
          </ToolExecutionProvider>
        </CommandProvider>
      </WebSocketProvider>
    </QueryClientProvider>
  )
}
