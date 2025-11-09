"use client";

import React from "react";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

interface ExecSummaryProps {
  context?: {
    projectId?: string;
    projectName?: string;
  };
}

export function ExecSummary({ context }: ExecSummaryProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-2 text-sm font-semibold text-ink-primary">
          Project Overview
        </h3>
        <p className="text-sm text-ink-secondary leading-relaxed">
          {context?.projectName || "Your project"} is on track. Latest
          deployment was successful with 95% test coverage. 3 PRs are ready for
          review.
        </p>
      </div>

      <div className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-tertiary">
          Key Metrics
        </h4>

        <MetricCard
          icon={<TrendingUp className="h-4 w-4 text-green-500" />}
          label="Deployment Success"
          value="95%"
          trend="up"
        />

        <MetricCard
          icon={<Activity className="h-4 w-4 text-blue-500" />}
          label="Active PRs"
          value="3"
        />

        <MetricCard
          icon={<TrendingDown className="h-4 w-4 text-amber-500" />}
          label="Code Coverage"
          value="87%"
          trend="stable"
        />
      </div>

      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-tertiary">
          Recent Activity
        </h4>
        <div className="space-y-2 text-sm">
          <ActivityItem time="2m ago" message="PR #104 merged to main" />
          <ActivityItem time="15m ago" message="Tests passed on feature/auth" />
          <ActivityItem
            time="1h ago"
            message="New spec created: User Dashboard"
          />
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  trend,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  trend?: "up" | "down" | "stable";
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-surface-secondary p-3">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm text-ink-secondary">{label}</span>
      </div>
      <div className="text-sm font-semibold text-ink-primary">{value}</div>
    </div>
  );
}

function ActivityItem({ time, message }: { time: string; message: string }) {
  return (
    <div className="flex items-start gap-2">
      <div className="mt-1 h-1.5 w-1.5 rounded-full bg-brand-primary" />
      <div className="flex-1">
        <p className="text-ink-secondary">{message}</p>
        <p className="text-xs text-ink-tertiary">{time}</p>
      </div>
    </div>
  );
}
