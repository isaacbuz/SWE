"use client";

import { CommandPalette } from "@/components/command/command-palette";
import { AIDockContent } from "@/components/ai-dock/ai-dock-content";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNavbar } from "@/components/app-shell/top-navbar";
import { LeftRail } from "@/components/app-shell/left-rail";
import { usePathname } from "next/navigation";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <ProtectedRoute>
      <div className="relative flex h-screen w-full flex-col">
        {/* Top Navbar */}
        <TopNavbar />

        <div className="flex flex-1 overflow-hidden">
          {/* Left Rail Navigation */}
          <LeftRail />

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">{children}</main>

          {/* AI Dock - Right Side */}
          <AIDockContent context={{ route: pathname || "/" }} />
        </div>

        {/* Command Palette - Global Overlay */}
        <CommandPalette />
      </div>
    </ProtectedRoute>
  );
}
