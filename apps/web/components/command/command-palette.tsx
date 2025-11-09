'use client'

import React, { useState, useMemo, useEffect } from 'react'
import { Command } from 'cmdk'
import { Search, FileText, Code, Zap, Clock, Wrench } from 'lucide-react'
import Fuse from 'fuse.js'
import { useUIStore } from '@/lib/stores/ui-store'
import { useCommand, CommandAction } from './command-provider'
import { useTools, groupToolsByCategory } from '@/lib/hooks/use-tools'
import { ToolSpec } from '@/lib/api/tools'
import { ToolExecutionDialog } from './tool-execution-dialog'
import { cn } from '@/lib/utils/cn'

export function CommandPalette() {
  const { commandPaletteOpen, closeCommandPalette } = useUIStore()
  const { actions, executeAction } = useCommand()
  const { recentCommands, addRecentCommand } = useUIStore()
  const [search, setSearch] = useState('')
  const [selectedTool, setSelectedTool] = useState<ToolSpec | null>(null)
  const { data: tools = [], isLoading: toolsLoading } = useTools()

  // Fuzzy search setup
  const fuse = useMemo(() => {
    return new Fuse(actions, {
      keys: ['label', 'description', 'keywords'],
      threshold: 0.3,
      includeScore: true,
    })
  }, [actions])

  // Search results
  const results = useMemo(() => {
    if (!search) {
      return actions
    }
    return fuse.search(search).map(result => result.item)
  }, [search, fuse, actions])

  // Convert tools to command actions
  const toolActions = useMemo(() => {
    return tools.map((tool): CommandAction => ({
      id: `tool-${tool.name}`,
      label: tool.name,
      description: tool.description,
      icon: <Wrench className="h-4 w-4" />,
      category: 'actions' as const,
      keywords: [tool.name, ...(tool.tags || []), tool.description],
      onExecute: () => {
        setSelectedTool(tool)
      },
    }))
  }, [tools])

  // Combine regular actions with tool actions
  const allActions = useMemo(() => {
    return [...actions, ...toolActions]
  }, [actions, toolActions])

  // Fuzzy search setup (include tool actions)
  const fuse = useMemo(() => {
    return new Fuse(allActions, {
      keys: ['label', 'description', 'keywords'],
      threshold: 0.3,
      includeScore: true,
    })
  }, [allActions])

  // Search results
  const results = useMemo(() => {
    if (!search) {
      return allActions
    }
    return fuse.search(search).map(result => result.item)
  }, [search, fuse, allActions])

  // Group tools by category
  const groupedTools = useMemo(() => {
    return groupToolsByCategory(tools)
  }, [tools])

  // Group results by category
  const grouped = useMemo(() => {
    const groups: Record<string, CommandAction[]> = {
      recent: [],
      actions: [],
      navigate: [],
      ai: [],
      tools: [],
    }

    results.forEach(action => {
      if (action.id.startsWith('tool-')) {
        groups.tools.push(action)
      } else if (recentCommands.includes(action.id)) {
        groups.recent.push(action)
      } else {
        groups[action.category].push(action)
      }
    })

    return groups
  }, [results, recentCommands])

  // Handle command execution
  const handleExecute = async (actionId: string) => {
    await executeAction(actionId)
    addRecentCommand(actionId)
    closeCommandPalette()
    setSearch('')
  }

  // Reset search when closed
  useEffect(() => {
    if (!commandPaletteOpen) {
      setSearch('')
    }
  }, [commandPaletteOpen])

  if (!commandPaletteOpen) return null

  return (
    <>
      <div
        className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-[20vh]"
        onClick={closeCommandPalette}
      >
      <Command
        className="w-full max-w-2xl rounded-xl border border-border-default bg-white shadow-e4"
        onClick={(e) => e.stopPropagation()}
        shouldFilter={false}
      >
        <div className="flex items-center border-b border-border-subtle px-4">
          <Search className="h-5 w-5 text-ink-tertiary" />
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder="Search or run command..."
            className="flex h-14 w-full bg-transparent px-4 text-sm outline-none placeholder:text-ink-tertiary"
          />
        </div>

        <Command.List className="max-h-[400px] overflow-y-auto p-2">
          <Command.Empty className="py-6 text-center text-sm text-ink-tertiary">
            No results found.
          </Command.Empty>

          {grouped.recent.length > 0 && (
            <Command.Group heading="Recent" className="mb-2">
              {grouped.recent.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => handleExecute(action.id)}
                />
              ))}
            </Command.Group>
          )}

          {grouped.actions.length > 0 && (
            <Command.Group heading="Actions" className="mb-2">
              {grouped.actions.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => handleExecute(action.id)}
                />
              ))}
            </Command.Group>
          )}

          {grouped.navigate.length > 0 && (
            <Command.Group heading="Navigate" className="mb-2">
              {grouped.navigate.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => handleExecute(action.id)}
                />
              ))}
            </Command.Group>
          )}

          {grouped.ai.length > 0 && (
            <Command.Group heading="AI Recipes" className="mb-2">
              {grouped.ai.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => handleExecute(action.id)}
                />
              ))}
            </Command.Group>
          )}

          {grouped.tools.length > 0 && (
            <Command.Group heading="Tools" className="mb-2">
              {grouped.tools.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => handleExecute(action.id)}
                />
              ))}
            </Command.Group>
          )}

          {toolsLoading && (
            <Command.Group heading="Loading tools..." className="mb-2">
              <div className="px-3 py-2 text-sm text-ink-tertiary">Loading available tools...</div>
            </Command.Group>
          )}
        </Command.List>

        <div className="flex items-center justify-between border-t border-border-subtle px-4 py-2 text-xs text-ink-tertiary">
          <div className="flex gap-4">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>⇧↵ Run in Dock</span>
          </div>
        </div>
      </Command>
    </div>

    {selectedTool && (
      <ToolExecutionDialog
        tool={selectedTool}
        onClose={() => {
          setSelectedTool(null)
          closeCommandPalette()
        }}
      />
    )}
    </>
  )
}

interface CommandItemProps {
  action: CommandAction
  onExecute: () => void
}

function CommandItem({ action, onExecute }: CommandItemProps) {
  const icons = {
    actions: <Zap className="h-4 w-4" />,
    navigate: <FileText className="h-4 w-4" />,
    ai: <Code className="h-4 w-4" />,
    recent: <Clock className="h-4 w-4" />,
  }

  return (
    <Command.Item
      onSelect={onExecute}
      className={cn(
        "flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2",
        "hover:bg-surface-secondary data-[selected=true]:bg-surface-secondary",
        "transition-colors duration-150"
      )}
    >
      <div className="text-ink-secondary">
        {action.icon || icons[action.category]}
      </div>
      <div className="flex-1">
        <div className="text-sm font-medium text-ink-primary">{action.label}</div>
        {action.description && (
          <div className="text-xs text-ink-tertiary">{action.description}</div>
        )}
      </div>
      {action.shortcut && (
        <kbd className="rounded border border-border-subtle bg-surface-tertiary px-2 py-1 text-xs font-mono text-ink-secondary">
          {action.shortcut}
        </kbd>
      )}
    </Command.Item>
  )
}
