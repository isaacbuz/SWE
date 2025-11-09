"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

export interface CommandAction {
  id: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  shortcut?: string;
  category: "actions" | "navigate" | "ai" | "recent";
  onExecute: () => void | Promise<void>;
  keywords?: string[];
}

interface CommandContextValue {
  actions: CommandAction[];
  registerAction: (action: CommandAction) => void;
  unregisterAction: (id: string) => void;
  executeAction: (id: string) => Promise<void>;
}

const CommandContext = createContext<CommandContextValue | null>(null);

export function CommandProvider({ children }: { children: ReactNode }) {
  const [actions, setActions] = useState<CommandAction[]>([]);

  const registerAction = useCallback((action: CommandAction) => {
    setActions((prev) => {
      const existing = prev.findIndex((a) => a.id === action.id);
      if (existing >= 0) {
        const newActions = [...prev];
        newActions[existing] = action;
        return newActions;
      }
      return [...prev, action];
    });
  }, []);

  const unregisterAction = useCallback((id: string) => {
    setActions((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const executeAction = useCallback(
    async (id: string) => {
      const action = actions.find((a) => a.id === id);
      if (action) {
        await action.onExecute();
      }
    },
    [actions],
  );

  return (
    <CommandContext.Provider
      value={{ actions, registerAction, unregisterAction, executeAction }}
    >
      {children}
    </CommandContext.Provider>
  );
}

export function useCommand() {
  const context = useContext(CommandContext);
  if (!context) {
    throw new Error("useCommand must be used within CommandProvider");
  }
  return context;
}
