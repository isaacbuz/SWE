"use client";

import React, { useState, useMemo, useEffect } from "react";
import { Command } from "cmdk";
import {
  Search,
  FileText,
  Code,
  Zap,
  Clock,
  Github,
  Terminal,
  Settings,
  Globe,
} from "lucide-react";
import Fuse from "fuse.js";
import { useUIStore } from "@/lib/stores/ui-store";
import { useCommand, CommandAction } from "./command-provider";
import { useToolRegistry } from "@/lib/hooks/use-tool-registry";
import { ToolExecutionForm } from "./tool-execution-form";
import { cn } from "@/lib/utils/cn";

export function CommandPalette() {
  const { commandPaletteOpen, closeCommandPalette } = useUIStore();
  const { actions, executeAction } = useCommand();
  const { recentCommands, addRecentCommand } = useUIStore();
  const { tools, toolsByCategory, loading: toolsLoading } = useToolRegistry();
  const [search, setSearch] = useState("");
  const [selectedTool, setSelectedTool] = useState<string | null>(null);

  // Fuzzy search setup
  const fuse = useMemo(() => {
    return new Fuse(actions, {
      keys: ["label", "description", "keywords"],
      threshold: 0.3,
      includeScore: true,
    });
  }, [actions]);

  // Search results
  const results = useMemo(() => {
    if (!search) {
      return actions;
    }
    return fuse.search(search).map((result) => result.item);
  }, [search, fuse, actions]);

  // Convert tools to command actions
  const toolActions = useMemo(() => {
    return tools.map((tool) => ({
      id: `tool:${tool.name}`,
      label: tool.name,
      description: tool.description,
      category: tool.category,
      icon: getCategoryIcon(tool.category),
      keywords: [
        tool.name,
        tool.description,
        ...tool.name.split(/(?=[A-Z])/).map((s) => s.toLowerCase()),
      ],
      shortcut: undefined,
    }));
  }, [tools]);

  // Combine regular actions with tool actions
  const allActions = useMemo(() => {
    return [...actions, ...toolActions];
  }, [actions, toolActions]);

  // Group results by category
  const grouped = useMemo(() => {
    const groups: Record<string, (CommandAction | (typeof toolActions)[0])[]> =
      {
        recent: [],
        actions: [],
        navigate: [],
        ai: [],
        github: [],
        code: [],
        cicd: [],
        external: [],
      };

    const searchResults = search
      ? new Fuse(allActions, {
          keys: ["label", "description", "keywords"],
          threshold: 0.3,
        })
          .search(search)
          .map((r) => r.item)
      : allActions;

    searchResults.forEach((action) => {
      if (recentCommands.includes(action.id)) {
        groups.recent.push(action);
      } else if (
        action.category === "github" ||
        action.category === "code" ||
        action.category === "cicd" ||
        action.category === "external"
      ) {
        groups[action.category].push(action);
      } else {
        groups[action.category]?.push(action);
      }
    });

    return groups;
  }, [search, allActions, recentCommands, toolActions]);

  // Handle tool execution
  const handleToolExecute = async (
    toolName: string,
    args: Record<string, any>,
  ) => {
    try {
      const response = await fetch("/api/v1/tools/execute", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tool: toolName,
          arguments: args,
        }),
      });

      if (!response.ok) {
        throw new Error("Tool execution failed");
      }

      const result = await response.json();
      console.log("Tool execution result:", result);
      // Show success notification
    } catch (error) {
      console.error("Tool execution error:", error);
      // Show error notification
    }
  };

  function getCategoryIcon(category: string) {
    switch (category) {
      case "github":
        return <Github className="h-4 w-4" />;
      case "code":
        return <Code className="h-4 w-4" />;
      case "cicd":
        return <Settings className="h-4 w-4" />;
      case "external":
        return <Globe className="h-4 w-4" />;
      default:
        return <Zap className="h-4 w-4" />;
    }
  }

  // Handle command execution
  const handleExecute = async (actionId: string) => {
    await executeAction(actionId);
    addRecentCommand(actionId);
    closeCommandPalette();
    setSearch("");
  };

  // Reset search when closed
  useEffect(() => {
    if (!commandPaletteOpen) {
      setSearch("");
    }
  }, [commandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  return (
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

          {grouped.github.length > 0 && (
            <Command.Group heading="🔧 GitHub Tools" className="mb-2">
              {grouped.github.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => {
                    if (action.id.startsWith("tool:")) {
                      const toolName = action.id.replace("tool:", "");
                      const tool = tools.find((t) => t.name === toolName);
                      if (tool) {
                        setSelectedTool(toolName);
                      }
                    } else {
                      handleExecute(action.id);
                    }
                  }}
                />
              ))}
            </Command.Group>
          )}

          {grouped.code.length > 0 && (
            <Command.Group heading="💻 Code Tools" className="mb-2">
              {grouped.code.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => {
                    if (action.id.startsWith("tool:")) {
                      const toolName = action.id.replace("tool:", "");
                      const tool = tools.find((t) => t.name === toolName);
                      if (tool) {
                        setSelectedTool(toolName);
                      }
                    } else {
                      handleExecute(action.id);
                    }
                  }}
                />
              ))}
            </Command.Group>
          )}

          {grouped.cicd.length > 0 && (
            <Command.Group heading="🏗️ CI/CD Tools" className="mb-2">
              {grouped.cicd.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => {
                    if (action.id.startsWith("tool:")) {
                      const toolName = action.id.replace("tool:", "");
                      const tool = tools.find((t) => t.name === toolName);
                      if (tool) {
                        setSelectedTool(toolName);
                      }
                    } else {
                      handleExecute(action.id);
                    }
                  }}
                />
              ))}
            </Command.Group>
          )}

          {grouped.external.length > 0 && (
            <Command.Group heading="🌐 External Tools" className="mb-2">
              {grouped.external.map((action) => (
                <CommandItem
                  key={action.id}
                  action={action}
                  onExecute={() => {
                    if (action.id.startsWith("tool:")) {
                      const toolName = action.id.replace("tool:", "");
                      const tool = tools.find((t) => t.name === toolName);
                      if (tool) {
                        setSelectedTool(toolName);
                      }
                    } else {
                      handleExecute(action.id);
                    }
                  }}
                />
              ))}
            </Command.Group>
          )}
        </Command.List>

        {selectedTool && (
          <ToolExecutionForm
            tool={tools.find((t) => t.name === selectedTool)!}
            onExecute={handleToolExecute}
            onClose={() => setSelectedTool(null)}
          />
        )}

        <div className="flex items-center justify-between border-t border-border-subtle px-4 py-2 text-xs text-ink-tertiary">
          <div className="flex gap-4">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>⇧↵ Run in Dock</span>
          </div>
        </div>
      </Command>
    </div>
  );
}

interface CommandItemProps {
  action: CommandAction;
  onExecute: () => void;
}

function CommandItem({ action, onExecute }: CommandItemProps) {
  const icons = {
    actions: <Zap className="h-4 w-4" />,
    navigate: <FileText className="h-4 w-4" />,
    ai: <Code className="h-4 w-4" />,
    recent: <Clock className="h-4 w-4" />,
  };

  return (
    <Command.Item
      onSelect={onExecute}
      className={cn(
        "flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2",
        "hover:bg-surface-secondary data-[selected=true]:bg-surface-secondary",
        "transition-colors duration-150",
      )}
    >
      <div className="text-ink-secondary">
        {action.icon || icons[action.category]}
      </div>
      <div className="flex-1">
        <div className="text-sm font-medium text-ink-primary">
          {action.label}
        </div>
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
  );
}
