"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  FolderKanban,
  Bot,
  BarChart3,
  Plug,
  Settings,
  ChevronLeft,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useState } from "react";

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
}

const navSections = [
  {
    title: "Workspace",
    items: [
      { icon: Home, label: "Home", href: "/" },
      { icon: FolderKanban, label: "Projects", href: "/projects" },
      { icon: Bot, label: "Agents", href: "/agents" },
      { icon: Zap, label: "Skills", href: "/skills" },
    ],
  },
  {
    title: "Insights",
    items: [
      { icon: BarChart3, label: "Analytics", href: "/analytics" },
      { icon: Plug, label: "Integrations", href: "/integrations" },
    ],
  },
  {
    title: "Settings",
    items: [{ icon: Settings, label: "Settings", href: "/settings" }],
  },
];

export function LeftRail() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "sticky top-16 h-[calc(100vh-4rem)] border-r border-border-subtle bg-surface-primary transition-all duration-200",
        collapsed ? "w-16" : "w-60",
      )}
    >
      <div className="flex h-full flex-col">
        {/* Navigation Sections */}
        <nav className="flex-1 space-y-6 p-4">
          {navSections.map((section) => (
            <div key={section.title}>
              {!collapsed && (
                <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-ink-tertiary">
                  {section.title}
                </h3>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/" && pathname.startsWith(item.href));
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                        "hover:bg-surface-tertiary hover:text-ink-primary",
                        isActive
                          ? "bg-brand-primary/10 text-brand-primary"
                          : "text-ink-secondary",
                        collapsed && "justify-center",
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      <Icon
                        className={cn(
                          "h-5 w-5 shrink-0",
                          isActive && "text-brand-primary",
                        )}
                      />
                      {!collapsed && <span>{item.label}</span>}
                      {isActive && !collapsed && (
                        <div className="ml-auto h-1.5 w-1.5 rounded-full bg-brand-primary" />
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Collapse Toggle */}
        <div className="border-t border-border-subtle p-4">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={cn(
              "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-ink-secondary transition-colors",
              "hover:bg-surface-tertiary hover:text-ink-primary",
              collapsed && "justify-center",
            )}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronLeft
              className={cn(
                "h-5 w-5 shrink-0 transition-transform",
                collapsed && "rotate-180",
              )}
            />
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}
