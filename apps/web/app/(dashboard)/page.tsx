"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useCommand } from "@/components/command/command-provider";
import {
  FileText,
  GitPullRequest,
  Settings,
  Home,
  FolderKanban,
  Bot,
  TrendingUp,
  DollarSign,
} from "lucide-react";
import { analyticsApi } from "@/lib/api/analytics";
import { projectsApi } from "@/lib/api/projects";
import { agentsApi } from "@/lib/api/agents";
import { issuesApi } from "@/lib/api/issues";
import Link from "next/link";

export default function HomePage() {
  const { registerAction } = useCommand();

  // Fetch dashboard metrics
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsApi.overview(),
  });

  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectsApi.list(),
  });

  const { data: agents } = useQuery({
    queryKey: ["agents"],
    queryFn: () => agentsApi.list(),
  });

  const { data: issues } = useQuery({
    queryKey: ["issues"],
    queryFn: () => issuesApi.list(),
  });

  // Register command actions
  useEffect(() => {
    registerAction({
      id: "new-spec",
      label: "/spec new - Create new specification",
      description: "Create a new specification document",
      icon: <FileText className="h-4 w-4" />,
      shortcut: "⌘N",
      category: "actions",
      onExecute: () => {
        console.log("Creating new spec...");
      },
      keywords: ["spec", "create", "new", "document"],
    });

    registerAction({
      id: "review-pr",
      label: "/review - Start code review",
      description: "Start an AI-powered code review",
      icon: <GitPullRequest className="h-4 w-4" />,
      shortcut: "⌘R",
      category: "actions",
      onExecute: () => {
        console.log("Starting review...");
      },
      keywords: ["review", "code", "pr", "pull request"],
    });

    registerAction({
      id: "nav-home",
      label: "Home",
      description: "Go to home page",
      icon: <Home className="h-4 w-4" />,
      category: "navigate",
      onExecute: () => {
        window.location.href = "/";
      },
      keywords: ["home", "dashboard"],
    });

    registerAction({
      id: "nav-settings",
      label: "Settings",
      description: "Open settings",
      icon: <Settings className="h-4 w-4" />,
      category: "navigate",
      onExecute: () => {
        window.location.href = "/settings";
      },
      keywords: ["settings", "preferences", "config"],
    });
  }, [registerAction]);

  const activeIssues = issues?.filter((i) => i.status !== "closed") || [];
  const completedIssues = issues?.filter((i) => i.status === "closed") || [];

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-ink-primary">Dashboard</h1>
          <p className="mt-2 text-lg text-ink-secondary">
            Overview of your AI-powered development platform
          </p>
        </header>

        {/* Metrics Grid */}
        <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Projects"
            value={projects?.length || 0}
            icon={<FolderKanban className="h-5 w-5" />}
            href="/projects"
            loading={!projects}
          />
          <MetricCard
            title="Active Agents"
            value={agents?.filter((a) => a.status === "running").length || 0}
            icon={<Bot className="h-5 w-5" />}
            href="/agents"
            loading={!agents}
          />
          <MetricCard
            title="Active Issues"
            value={activeIssues.length}
            icon={<TrendingUp className="h-5 w-5" />}
            href="/projects"
            loading={!issues}
          />
          <MetricCard
            title="Total Cost"
            value={`$${overview?.total_cost_usd?.toFixed(2) || "0.00"}`}
            icon={<DollarSign className="h-5 w-5" />}
            href="/analytics/costs"
            loading={overviewLoading}
          />
        </div>

        {/* Additional Metrics */}
        {overview && (
          <div className="mb-8 grid gap-6 md:grid-cols-3">
            <StatCard
              title="Completed Issues"
              value={completedIssues.length}
              subtitle={`${overview.completed_issues || 0} total`}
            />
            <StatCard
              title="Avg Review Time"
              value={`${overview.avg_review_time_minutes || 0}m`}
              subtitle="Average PR review"
            />
            <StatCard
              title="Total Agents"
              value={agents?.length || 0}
              subtitle={`${agents?.filter((a) => a.status === "running").length || 0} running`}
            />
          </div>
        )}

        {/* Quick Actions */}
        <div className="mb-8 rounded-xl border border-border-subtle bg-surface-secondary p-6">
          <h2 className="mb-4 text-xl font-semibold text-ink-primary">
            Quick Actions
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Link
              href="/projects/new"
              className="rounded-lg border border-border-subtle bg-white p-4 transition-shadow hover:shadow-e2"
            >
              <div className="mb-2 flex items-center gap-2">
                <FolderKanban className="h-5 w-5 text-brand-primary" />
                <h3 className="font-medium text-ink-primary">New Project</h3>
              </div>
              <p className="text-sm text-ink-secondary">Create a new project</p>
            </Link>
            <Link
              href="/agents/compose"
              className="rounded-lg border border-border-subtle bg-white p-4 transition-shadow hover:shadow-e2"
            >
              <div className="mb-2 flex items-center gap-2">
                <Bot className="h-5 w-5 text-brand-primary" />
                <h3 className="font-medium text-ink-primary">Compose Crew</h3>
              </div>
              <p className="text-sm text-ink-secondary">Create agent crew</p>
            </Link>
            <Link
              href="/analytics"
              className="rounded-lg border border-border-subtle bg-white p-4 transition-shadow hover:shadow-e2"
            >
              <div className="mb-2 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-brand-primary" />
                <h3 className="font-medium text-ink-primary">View Analytics</h3>
              </div>
              <p className="text-sm text-ink-secondary">
                See performance metrics
              </p>
            </Link>
            <Link
              href="/settings"
              className="rounded-lg border border-border-subtle bg-white p-4 transition-shadow hover:shadow-e2"
            >
              <div className="mb-2 flex items-center gap-2">
                <Settings className="h-5 w-5 text-brand-primary" />
                <h3 className="font-medium text-ink-primary">Settings</h3>
              </div>
              <p className="text-sm text-ink-secondary">
                Configure preferences
              </p>
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        {projects && projects.length > 0 && (
          <div className="rounded-xl border border-border-subtle bg-surface-secondary p-6">
            <h2 className="mb-4 text-xl font-semibold text-ink-primary">
              Recent Projects
            </h2>
            <div className="space-y-3">
              {projects.slice(0, 5).map((project) => (
                <Link
                  key={project.project_id}
                  href={`/projects/${project.project_id}`}
                  className="flex items-center justify-between rounded-lg border border-border-subtle bg-white p-4 transition-shadow hover:shadow-e2"
                >
                  <div>
                    <h3 className="font-medium text-ink-primary">
                      {project.name}
                    </h3>
                    {project.description && (
                      <p className="text-sm text-ink-secondary">
                        {project.description}
                      </p>
                    )}
                  </div>
                  <span className="rounded-full bg-surface-tertiary px-3 py-1 text-xs font-medium text-ink-secondary">
                    {project.status}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon,
  href,
  loading,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  href?: string;
  loading?: boolean;
}) {
  const content = (
    <div className="rounded-lg border border-border-subtle bg-white p-6 transition-shadow hover:shadow-e2">
      <div className="mb-4 flex items-center justify-between">
        <div className="rounded-lg bg-surface-tertiary p-2 text-brand-primary">
          {icon}
        </div>
      </div>
      <h3 className="mb-1 text-sm font-medium text-ink-secondary">{title}</h3>
      {loading ? (
        <div className="h-8 w-20 animate-pulse rounded bg-surface-tertiary" />
      ) : (
        <p className="text-3xl font-bold text-ink-primary">{value}</p>
      )}
    </div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}

function StatCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-white p-6">
      <h3 className="mb-1 text-sm font-medium text-ink-secondary">{title}</h3>
      <p className="text-2xl font-bold text-ink-primary">{value}</p>
      {subtitle && <p className="mt-1 text-xs text-ink-tertiary">{subtitle}</p>}
    </div>
  );
}

function DemoCard({
  title,
  description,
  shortcut,
}: {
  title: string;
  description: string;
  shortcut: string;
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-white p-6 shadow-e1 transition-shadow hover:shadow-e2">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-ink-primary">{title}</h3>
        <kbd className="rounded border border-border-subtle bg-surface-tertiary px-2 py-1 font-mono text-sm text-ink-secondary">
          {shortcut}
        </kbd>
      </div>
      <p className="text-sm text-ink-secondary">{description}</p>
    </div>
  );
}

function FeatureItem({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <li className="flex items-start gap-3">
      <div className="mt-1 h-2 w-2 rounded-full bg-brand-primary" />
      <div>
        <h4 className="font-medium text-ink-primary">{title}</h4>
        <p className="text-sm text-ink-tertiary">{description}</p>
      </div>
    </li>
  );
}
