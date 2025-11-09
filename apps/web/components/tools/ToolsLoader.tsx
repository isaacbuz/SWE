'use client'

import { useEffect } from 'react'
import { useOpenAPITools } from '@/hooks/useOpenAPITools'

/**
 * Component to load and register OpenAPI tools in command palette
 * Should be included in the app layout
 */
export function ToolsLoader() {
  const { loading, error } = useOpenAPITools()

  useEffect(() => {
    if (error) {
      console.error('Failed to load tools:', error)
    }
  }, [error])

  // This component doesn't render anything, it just loads tools
  return null
}

