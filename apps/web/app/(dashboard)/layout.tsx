'use client'

import { CommandPalette } from '@/components/command/command-palette'
import { AIDockContent } from '@/components/ai-dock/ai-dock-content'
import { ToolsLoader } from '@/components/tools/ToolsLoader'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="relative flex h-screen w-full">
      {/* Tools Loader - Auto-loads tools into command palette */}
      <ToolsLoader />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* AI Dock - Right Side */}
      <AIDockContent context={{ route: '/' }} />

      {/* Command Palette - Global Overlay */}
      <CommandPalette />
    </div>
  )
}
