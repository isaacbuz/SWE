"use client";

import { useState } from 'react';
import { ChevronRight, Settings, Sparkles, Send } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface ActionChipProps {
  children: React.ReactNode;
  onClick?: () => void;
}

function ActionChip({ children, onClick }: ActionChipProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 rounded-lg border border-border-default bg-surface-secondary px-3 py-2 text-sm text-ink-secondary transition-colors hover:border-brand-primary hover:bg-brand-primary/5 hover:text-brand-primary"
    >
      <Sparkles className="h-4 w-4" />
      <span>{children}</span>
    </button>
  );
}

const tabs = ['Exec Summary', 'Risks', 'Actions'];

export function AIDock() {
  const [collapsed, setCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [prompt, setPrompt] = useState('');

  if (collapsed) {
    return (
      <aside className="sticky top-16 h-[calc(100vh-4rem)] w-12 border-l border-border-subtle bg-surface-primary">
        <button
          onClick={() => setCollapsed(false)}
          className="flex h-12 w-full items-center justify-center text-ink-tertiary hover:bg-surface-tertiary hover:text-ink-primary transition-colors"
          title="Expand AI Dock"
        >
          <ChevronRight className="h-5 w-5 rotate-180" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="sticky top-16 h-[calc(100vh-4rem)] w-[360px] border-l border-border-subtle bg-surface-primary">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border-subtle p-4">
          <div>
            <h2 className="text-sm font-semibold text-ink-primary">AI Copilot</h2>
            <p className="text-xs text-ink-tertiary">Context-aware assistant</p>
          </div>
          <div className="flex items-center gap-1">
            <button className="p-2 rounded-md hover:bg-surface-tertiary transition-colors">
              <Settings className="h-4 w-4 text-ink-tertiary" />
            </button>
            <button 
              onClick={() => setCollapsed(true)}
              className="p-2 rounded-md hover:bg-surface-tertiary transition-colors"
            >
              <ChevronRight className="h-4 w-4 text-ink-tertiary" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border-subtle">
          {tabs.map((tab, index) => (
            <button
              key={tab}
              onClick={() => setActiveTab(index)}
              className={cn(
                "flex-1 px-4 py-3 text-sm font-medium transition-colors",
                activeTab === index
                  ? "border-b-2 border-brand-primary text-brand-primary"
                  : "text-ink-tertiary hover:text-ink-secondary"
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 0 && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border-default bg-surface-secondary p-4">
                <h3 className="mb-2 text-sm font-semibold text-ink-primary">Project Status</h3>
                <p className="text-sm text-ink-secondary">
                  3 active workflows, 12 pending tasks. Overall health: Good.
                </p>
              </div>
              <div className="rounded-lg border border-border-default bg-surface-secondary p-4">
                <h3 className="mb-2 text-sm font-semibold text-ink-primary">Recent Activity</h3>
                <ul className="space-y-2 text-sm text-ink-secondary">
                  <li className="flex items-start gap-2">
                    <span className="text-status-success">•</span>
                    <span>PR #104 merged successfully</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-status-warning">•</span>
                    <span>2 tests failing in test suite</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-status-info">•</span>
                    <span>New spec created: Auth flow</span>
                  </li>
                </ul>
              </div>
            </div>
          )}

          {activeTab === 1 && (
            <div className="space-y-4">
              <div className="rounded-lg border border-status-warning/20 bg-status-warning/5 p-4">
                <h3 className="mb-2 text-sm font-semibold text-status-warning">Medium Risk</h3>
                <p className="text-sm text-ink-secondary">
                  Database migration pending review. Could impact production.
                </p>
              </div>
              <div className="rounded-lg border border-border-default bg-surface-secondary p-4">
                <h3 className="mb-2 text-sm font-semibold text-ink-primary">All Clear</h3>
                <p className="text-sm text-ink-secondary">
                  No critical risks detected in current workflows.
                </p>
              </div>
            </div>
          )}

          {activeTab === 2 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-ink-primary">Suggested Actions</h3>
              <ActionChip onClick={() => console.log('Action 1')}>
                Summarize PR #104
              </ActionChip>
              <ActionChip onClick={() => console.log('Action 2')}>
                Generate test plan
              </ActionChip>
              <ActionChip onClick={() => console.log('Action 3')}>
                Estimate costs
              </ActionChip>
              <ActionChip onClick={() => console.log('Action 4')}>
                Review code changes
              </ActionChip>
            </div>
          )}
        </div>

        {/* Footer - Prompt Bar */}
        <div className="border-t border-border-subtle p-4">
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask AI..."
                rows={1}
                className="w-full resize-none rounded-md border border-border-default bg-surface-secondary px-3 py-2 text-sm text-ink-primary placeholder:text-ink-tertiary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    // TODO: Send prompt
                    console.log('Send prompt:', prompt);
                    setPrompt('');
                  }
                }}
              />
            </div>
            <button
              onClick={() => {
                // TODO: Send prompt
                console.log('Send prompt:', prompt);
                setPrompt('');
              }}
              disabled={!prompt.trim()}
              className="rounded-md bg-brand-primary p-2 text-white transition-colors hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
