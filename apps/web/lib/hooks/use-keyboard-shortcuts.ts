'use client'

import { useEffect } from 'react'
import { useUIStore } from '@/lib/stores/ui-store'
import { matchesShortcut } from '@/lib/shortcuts'
import { useRouter } from 'next/navigation'

/**
 * Global keyboard shortcuts handler
 */
export function useKeyboardShortcuts() {
  const router = useRouter()
  const { 
    toggleCommandPalette, 
    toggleAIDock, 
    toggleLeftRail,
    commandPaletteOpen,
  } = useUIStore()

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields
      const target = event.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow Command Palette shortcut even in inputs
        if (!matchesShortcut(event, 'COMMAND_PALETTE')) {
          return
        }
      }

      // Command Palette (⌘K)
      if (matchesShortcut(event, 'COMMAND_PALETTE')) {
        event.preventDefault()
        toggleCommandPalette()
        return
      }

      // Don't process other shortcuts if Command Palette is open
      if (commandPaletteOpen) {
        if (event.key === 'Escape') {
          event.preventDefault()
          toggleCommandPalette()
        }
        return
      }

      // AI Dock (⌘/)
      if (matchesShortcut(event, 'TOGGLE_AI_DOCK')) {
        event.preventDefault()
        toggleAIDock()
        return
      }

      // Left Rail (⌘B)
      if (matchesShortcut(event, 'TOGGLE_LEFT_RAIL')) {
        event.preventDefault()
        toggleLeftRail()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [
    router,
    toggleCommandPalette,
    toggleAIDock,
    toggleLeftRail,
    commandPaletteOpen,
  ])
}
