"use client";

import { useTheme } from "@/lib/theme/theme-provider";
import { Check, Moon, Sun, Monitor } from "lucide-react";

const tabs = ["Account", "Team", "Appearance", "Notifications"];

export default function SettingsPage() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-ink-primary">Settings</h1>
        <p className="mt-2 text-ink-secondary">
          Manage your account and preferences
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-border-subtle">
        <div className="flex gap-6">
          {tabs.map((tab, index) => (
            <button
              key={tab}
              className={
                "pb-4 text-sm font-medium transition-colors " +
                (index === 2
                  ? "border-b-2 border-brand-primary text-brand-primary"
                  : "text-ink-tertiary hover:text-ink-secondary")
              }
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Appearance Settings */}
      <div className="max-w-2xl space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-ink-primary">Theme</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            Choose your preferred theme for the interface
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <ThemeOption
            icon={<Sun className="h-5 w-5" />}
            label="Light"
            description="Bright and clean"
            active={theme === "light"}
            onClick={() => setTheme("light")}
          />
          <ThemeOption
            icon={<Moon className="h-5 w-5" />}
            label="Dark"
            description="Easy on the eyes"
            active={theme === "dark"}
            onClick={() => setTheme("dark")}
          />
          <ThemeOption
            icon={<Monitor className="h-5 w-5" />}
            label="System"
            description="Match OS theme"
            active={theme === "system"}
            onClick={() => setTheme("system")}
          />
        </div>

        <div className="rounded-lg border border-border-default bg-surface-secondary p-4">
          <p className="text-sm text-ink-secondary">
            Current theme:{" "}
            <strong className="text-ink-primary">{resolvedTheme}</strong>
          </p>
        </div>

        <div className="border-t border-border-subtle pt-6">
          <h2 className="text-lg font-semibold text-ink-primary">Display</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            Customize how information is displayed
          </p>

          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-ink-primary">
                  Compact mode
                </p>
                <p className="text-xs text-ink-tertiary">
                  Show more content on screen
                </p>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-surface-tertiary transition-colors hover:bg-border-default">
                <span className="inline-block h-4 w-4 translate-x-1 transform rounded-full bg-white shadow-e1 transition-transform" />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-ink-primary">
                  Animations
                </p>
                <p className="text-xs text-ink-tertiary">
                  Enable interface animations
                </p>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-brand-primary transition-colors">
                <span className="inline-block h-4 w-4 translate-x-6 transform rounded-full bg-white shadow-e1 transition-transform" />
              </button>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t border-border-subtle pt-6">
          <button className="rounded-md border border-border-default px-4 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-tertiary transition-colors">
            Reset to defaults
          </button>
          <button className="rounded-md bg-brand-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-hover">
            Save changes
          </button>
        </div>
      </div>
    </div>
  );
}

function ThemeOption({
  icon,
  label,
  description,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={
        "relative flex flex-col items-center gap-3 rounded-lg border p-6 transition-all " +
        (active
          ? "border-brand-primary bg-brand-primary/5"
          : "border-border-default bg-surface-secondary hover:border-brand-primary/50")
      }
    >
      {active && (
        <div className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-brand-primary text-white">
          <Check className="h-3 w-3" />
        </div>
      )}
      <div
        className={
          "flex h-10 w-10 items-center justify-center rounded-full " +
          (active
            ? "bg-brand-primary/10 text-brand-primary"
            : "bg-surface-tertiary text-ink-tertiary")
        }
      >
        {icon}
      </div>
      <div className="text-center">
        <p
          className={
            "text-sm font-medium " +
            (active ? "text-brand-primary" : "text-ink-primary")
          }
        >
          {label}
        </p>
        <p className="text-xs text-ink-tertiary">{description}</p>
      </div>
    </button>
  );
}
