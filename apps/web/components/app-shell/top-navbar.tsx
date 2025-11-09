"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Bell, User, Command } from "lucide-react";
import { cn } from "@/lib/utils/cn";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/projects", label: "Projects" },
  { href: "/agents", label: "Agents" },
  { href: "/analytics", label: "Analytics" },
];

export function TopNavbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border-subtle bg-surface-primary/95 backdrop-blur supports-[backdrop-filter]:bg-surface-primary/80">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Left Section */}
        <div className="flex items-center gap-8">
          {/* Brand */}
          <Link
            href="/"
            className="flex items-center gap-2 text-xl font-bold text-ink-primary hover:text-brand-primary transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-primary text-white">
              AI
            </div>
            <span className="font-display">AgentOS</span>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive =
                pathname === link.href ||
                (link.href !== "/" && pathname.startsWith(link.href));

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                    "hover:bg-surface-tertiary hover:text-ink-primary",
                    isActive
                      ? "bg-surface-tertiary text-ink-primary"
                      : "text-ink-secondary",
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Center - Command Trigger */}
        <button
          className="hidden lg:flex items-center gap-2 px-4 py-2 rounded-md bg-surface-tertiary text-ink-tertiary hover:bg-surface-tertiary hover:text-ink-primary transition-colors group"
          onClick={() => {
            // TODO: Open command palette
            console.log("Open command palette");
          }}
        >
          <Search className="h-4 w-4" />
          <span className="text-sm">Search or run command...</span>
          <kbd className="ml-2 inline-flex h-5 items-center gap-1 rounded border border-border-default bg-surface-primary px-1.5 font-mono text-xs text-ink-tertiary">
            <Command className="h-3 w-3" />K
          </kbd>
        </button>

        {/* Right Section */}
        <div className="flex items-center gap-3">
          {/* Runs Indicator */}
          <button className="relative p-2 rounded-md hover:bg-surface-tertiary transition-colors">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-status-success animate-pulse" />
              <span className="text-sm font-medium text-ink-secondary">
                3 active
              </span>
            </div>
          </button>

          {/* Notifications */}
          <button className="relative p-2 rounded-md hover:bg-surface-tertiary transition-colors">
            <Bell className="h-5 w-5 text-ink-secondary" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-status-danger" />
          </button>

          {/* User Menu */}
          <button className="flex items-center gap-2 p-2 rounded-md hover:bg-surface-tertiary transition-colors">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-primary text-white">
              <User className="h-5 w-5" />
            </div>
          </button>
        </div>
      </div>
    </nav>
  );
}
