"use client";

import React from "react";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface RiskListProps {
  context?: {
    projectId?: string;
  };
}

export function RiskList({ context }: RiskListProps) {
  const risks = [
    {
      severity: "high" as const,
      title: "Dependency Vulnerability",
      description:
        'Package "axios" has a known security vulnerability. Update to v1.6.0+',
      file: "package.json",
    },
    {
      severity: "medium" as const,
      title: "Test Coverage Below Target",
      description: "auth.ts has only 65% coverage. Target is 80%",
      file: "src/auth.ts",
    },
    {
      severity: "low" as const,
      title: "API Response Time",
      description: "/api/users endpoint averaging 2.3s. Consider caching",
      file: "api/users.ts",
    },
  ];

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-ink-primary">
        Risk Indicators
      </h3>

      {risks.length === 0 ? (
        <div className="rounded-lg border border-border-subtle bg-surface-secondary p-4 text-center">
          <p className="text-sm text-ink-tertiary">No risks detected</p>
        </div>
      ) : (
        <div className="space-y-2">
          {risks.map((risk, index) => (
            <RiskCard key={index} risk={risk} />
          ))}
        </div>
      )}
    </div>
  );
}

interface Risk {
  severity: "high" | "medium" | "low";
  title: string;
  description: string;
  file: string;
}

function RiskCard({ risk }: { risk: Risk }) {
  const severityConfig = {
    high: {
      icon: AlertTriangle,
      color: "text-red-500",
      bg: "bg-red-50",
      border: "border-red-200",
    },
    medium: {
      icon: AlertCircle,
      color: "text-amber-500",
      bg: "bg-amber-50",
      border: "border-amber-200",
    },
    low: {
      icon: Info,
      color: "text-blue-500",
      bg: "bg-blue-50",
      border: "border-blue-200",
    },
  };

  const config = severityConfig[risk.severity];
  const Icon = config.icon;

  return (
    <div className={cn("rounded-lg border p-3", config.border, config.bg)}>
      <div className="flex items-start gap-2">
        <Icon className={cn("h-4 w-4 mt-0.5", config.color)} />
        <div className="flex-1 space-y-1">
          <h4 className="text-sm font-medium text-ink-primary">{risk.title}</h4>
          <p className="text-xs text-ink-secondary">{risk.description}</p>
          <p className="font-mono text-xs text-ink-tertiary">{risk.file}</p>
        </div>
      </div>
    </div>
  );
}
