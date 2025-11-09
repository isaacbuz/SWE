'use client'

import { useEffect, useCallback } from 'react'
import { useWebSocket } from './websocket-provider'

/**
 * Hook for subscribing to WebSocket events
 */
export function useWebSocketEvent<T = any>(
  event: string,
  handler: (data: T) => void,
  dependencies: any[] = []
) {
  const { socket, connected } = useWebSocket()

  useEffect(() => {
    if (!socket || !connected) {
      return
    }

    socket.on(event, handler)

    return () => {
      socket.off(event, handler)
    }
  }, [socket, connected, event, ...dependencies])
}

/**
 * Hook for AI Dock real-time updates
 */
export function useAIDockUpdates(handler: (update: any) => void) {
  useWebSocketEvent('ai:suggestion', handler)
}

/**
 * Hook for project real-time updates
 */
export function useProjectUpdates(projectId: string, handler: (update: any) => void) {
  useWebSocketEvent('project:update', (data: any) => {
    if (data.projectId === projectId) {
      handler(data)
    }
  }, [projectId])
}

/**
 * Hook for agent real-time updates
 */
export function useAgentUpdates(agentId: string, handler: (update: any) => void) {
  useWebSocketEvent('agent:update', (data: any) => {
    if (data.agentId === agentId) {
      handler(data)
    }
  }, [agentId])
}

/**
 * Hook for emitting WebSocket events
 */
export function useEmitWebSocket() {
  const { socket, connected } = useWebSocket()

  return useCallback((event: string, data: any) => {
    if (socket && connected) {
      socket.emit(event, data)
    } else {
      console.warn('WebSocket not connected, cannot emit event:', event)
    }
  }, [socket, connected])
}

