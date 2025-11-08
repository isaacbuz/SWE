'use client'

import { useEffect } from 'react'
import { useUIStore } from '@/lib/stores/ui-store'
import { matchesShortcut } from '@/lib/shortcuts'

/**
 * Hook to setup Command Palette keyboard shortcut (⌘K)
 */
export function useCommandPalette() {
  const { toggleCommandPalette } = useUIStore()

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (matchesShortcut(event, 'COMMAND_PALETTE')) {
        event.preventDefault()
        toggleCommandPalette()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggleCommandPalette])
}
