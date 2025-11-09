'use client'

import { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { CommandProvider } from '@/components/command/command-provider'
import { WebSocketProvider } from '@/lib/websocket/websocket-provider'
import { AuthProvider } from '@/lib/auth/auth-context'
import { ErrorBoundary } from '@/components/error-boundary'
import { useKeyboardShortcuts } from '@/lib/hooks/use-keyboard-shortcuts'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.status >= 400 && error?.status < 500) {
          return false
        }
        return failureCount < 3
      },
    },
  },
})

function KeyboardShortcutsHandler() {
  useKeyboardShortcuts()
  return null
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <WebSocketProvider>
            <CommandProvider>
              <KeyboardShortcutsHandler />
              {children}
              <ReactQueryDevtools initialIsOpen={false} />
            </CommandProvider>
          </WebSocketProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
