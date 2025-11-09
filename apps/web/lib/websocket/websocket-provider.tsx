'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { io, Socket } from 'socket.io-client'

interface WebSocketContextType {
  socket: Socket | null
  connected: boolean
  error: Error | null
}

const WebSocketContext = createContext<WebSocketContextType>({
  socket: null,
  connected: false,
  error: null,
})

export function useWebSocket() {
  return useContext(WebSocketContext)
}

interface WebSocketProviderProps {
  children: ReactNode
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Get WebSocket URL from environment or use default
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:4000'

    // Initialize Socket.io client
    const newSocket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
      timeout: 20000,
    })

    // Connection event handlers
    newSocket.on('connect', () => {
      setConnected(true)
      setError(null)
      console.log('WebSocket connected')
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
      console.log('WebSocket disconnected')
    })

    newSocket.on('connect_error', (err) => {
      setError(err)
      setConnected(false)
      console.error('WebSocket connection error:', err)
    })

    newSocket.on('error', (err) => {
      setError(err)
      console.error('WebSocket error:', err)
    })

    setSocket(newSocket)

    // Cleanup on unmount
    return () => {
      newSocket.close()
    }
  }, [])

  return (
    <WebSocketContext.Provider value={{ socket, connected, error }}>
      {children}
    </WebSocketContext.Provider>
  )
}

