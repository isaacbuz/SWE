"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Sun, Moon, Monitor, Palette, Layout, Type } from "lucide-react";
import { useState } from "react";

export default function AppearanceSettingsPage() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Appearance</h1>
        <p className="text-muted-foreground">
          Customize the look and feel of your workspace
        </p>
      </div>

      {/* Theme Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
          <CardDescription>Choose your preferred color scheme</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => setTheme("light")}
              className={`flex flex-col items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                theme === "light"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
            >
              <Sun className="h-8 w-8" />
              <div className="text-center">
                <p className="font-medium">Light</p>
                <p className="text-xs text-muted-foreground">
                  Bright and clean
                </p>
              </div>
            </button>

            <button
              onClick={() => setTheme("dark")}
              className={`flex flex-col items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                theme === "dark"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
            >
              <Moon className="h-8 w-8" />
              <div className="text-center">
                <p className="font-medium">Dark</p>
                <p className="text-xs text-muted-foreground">
                  Easy on the eyes
                </p>
              </div>
            </button>

            <button
              onClick={() => setTheme("system")}
              className={`flex flex-col items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                theme === "system"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
            >
              <Monitor className="h-8 w-8" />
              <div className="text-center">
                <p className="font-medium">System</p>
                <p className="text-xs text-muted-foreground">
                  Match OS setting
                </p>
              </div>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Color Scheme */}
      <Card>
        <CardHeader>
          <CardTitle>Color Scheme</CardTitle>
          <CardDescription>Select your preferred accent color</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-6 gap-3">
            {[
              { name: "Indigo", color: "#4F46E5" },
              { name: "Blue", color: "#3B82F6" },
              { name: "Green", color: "#10B981" },
              { name: "Purple", color: "#8B5CF6" },
              { name: "Pink", color: "#EC4899" },
              { name: "Orange", color: "#F59E0B" },
            ].map((colorScheme) => (
              <button
                key={colorScheme.name}
                className="group relative aspect-square rounded-lg border-2 border-border p-1 transition-all hover:border-primary"
                title={colorScheme.name}
              >
                <div
                  className="h-full w-full rounded-md"
                  style={{ backgroundColor: colorScheme.color }}
                />
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Typography */}
      <Card>
        <CardHeader>
          <CardTitle>Typography</CardTitle>
          <CardDescription>
            Customize font settings for better readability
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fontSize">Font Size</Label>
            <div className="relative">
              <Type className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Select id="fontSize" defaultValue="medium" className="pl-9">
                <option value="small">Small</option>
                <option value="medium">Medium</option>
                <option value="large">Large</option>
                <option value="xlarge">Extra Large</option>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="codeFont">Code Font</Label>
            <Select id="codeFont" defaultValue="jetbrains">
              <option value="jetbrains">JetBrains Mono</option>
              <option value="fira">Fira Code</option>
              <option value="cascadia">Cascadia Code</option>
              <option value="sourcecodepro">Source Code Pro</option>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Enable Ligatures</p>
              <p className="text-sm text-muted-foreground">
                Use programming ligatures in code blocks
              </p>
            </div>
            <input type="checkbox" defaultChecked className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Layout Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Layout</CardTitle>
          <CardDescription>
            Configure workspace layout preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="sidebarPosition">Sidebar Position</Label>
            <div className="relative">
              <Layout className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Select id="sidebarPosition" defaultValue="left" className="pl-9">
                <option value="left">Left</option>
                <option value="right">Right</option>
              </Select>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Compact Mode</p>
              <p className="text-sm text-muted-foreground">
                Reduce spacing for more content on screen
              </p>
            </div>
            <input type="checkbox" className="h-4 w-4" />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Show Breadcrumbs</p>
              <p className="text-sm text-muted-foreground">
                Display navigation breadcrumbs at the top
              </p>
            </div>
            <input type="checkbox" defaultChecked className="h-4 w-4" />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Auto-hide Sidebar</p>
              <p className="text-sm text-muted-foreground">
                Automatically collapse sidebar when not in use
              </p>
            </div>
            <input type="checkbox" className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Accessibility */}
      <Card>
        <CardHeader>
          <CardTitle>Accessibility</CardTitle>
          <CardDescription>Enhance accessibility features</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">High Contrast Mode</p>
              <p className="text-sm text-muted-foreground">
                Increase contrast for better visibility
              </p>
            </div>
            <input type="checkbox" className="h-4 w-4" />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Reduce Motion</p>
              <p className="text-sm text-muted-foreground">
                Minimize animations and transitions
              </p>
            </div>
            <input type="checkbox" className="h-4 w-4" />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Screen Reader Support</p>
              <p className="text-sm text-muted-foreground">
                Enhanced labels for screen readers
              </p>
            </div>
            <input type="checkbox" defaultChecked className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button size="lg">Save Preferences</Button>
      </div>
    </div>
  );
}
