import { ArrowLeft, Settings, Plus } from "lucide-react";
import Link from "next/link";

const tabs = ["Board", "Specs", "PRs", "Tests"];

const columns = [
  {
    title: "To Do",
    count: 12,
    items: [
      { id: "54", title: "Implement auth flow", priority: "High", assignee: "Codegen Agent" },
      { id: "55", title: "Add payment gateway", priority: "Medium", assignee: "Backend Agent" },
    ],
  },
  {
    title: "In Progress",
    count: 5,
    items: [
      { id: "52", title: "Database schema migration", priority: "High", assignee: "DevOps Agent" },
    ],
  },
  {
    title: "Review",
    count: 3,
    items: [
      { id: "48", title: "API endpoint refactor", priority: "Medium", assignee: "Code Review Agent" },
    ],
  },
  {
    title: "Done",
    count: 28,
    items: [
      { id: "45", title: "User registration flow", priority: "High", assignee: "Codegen Agent" },
    ],
  },
];

export default async function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  return (
    <div className="space-y-6">
      {/* Breadcrumb & Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/projects"
            className="rounded-md p-2 hover:bg-surface-tertiary transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-ink-secondary" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold text-ink-primary">E-Commerce Platform</h1>
              <span className="rounded-full border border-status-success/20 bg-status-success/10 px-2 py-1 text-xs font-medium text-status-success">
                Active
              </span>
            </div>
            <p className="mt-1 text-sm text-ink-tertiary">Project #{id}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-tertiary transition-colors">
            <Plus className="h-4 w-4" />
            New Spec
          </button>
          <button className="flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-tertiary transition-colors">
            <Plus className="h-4 w-4" />
            New PR
          </button>
          <button className="rounded-md p-2 hover:bg-surface-tertiary transition-colors">
            <Settings className="h-5 w-5 text-ink-secondary" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border-subtle">
        <div className="flex gap-6">
          {tabs.map((tab, index) => (
            <button
              key={tab}
              className={"pb-4 text-sm font-medium transition-colors " + (index === 0 ? "border-b-2 border-brand-primary text-brand-primary" : "text-ink-tertiary hover:text-ink-secondary")}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Board View */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
        {columns.map((column) => (
          <div key={column.title} className="rounded-lg border border-border-default bg-surface-secondary p-4">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-ink-primary">{column.title}</h3>
              <span className="text-xs text-ink-tertiary">{column.count}</span>
            </div>
            <div className="space-y-3">
              {column.items.map((item) => (
                <IssueCard key={item.id} item={item} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function IssueCard({ item }: { item: { id: string; title: string; priority: string; assignee: string } }) {
  const priorityColors = {
    High: "border-status-danger/20 bg-status-danger/5 text-status-danger",
    Medium: "border-status-warning/20 bg-status-warning/5 text-status-warning",
    Low: "border-status-info/20 bg-status-info/5 text-status-info",
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-primary p-3 hover:border-brand-primary transition-colors cursor-pointer">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-ink-primary">#{item.id} {item.title}</h4>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span className={"rounded-full border px-2 py-0.5 text-xs font-medium " + priorityColors[item.priority as keyof typeof priorityColors]}>
          {item.priority}
        </span>
      </div>
      <p className="mt-2 text-xs text-ink-tertiary">{item.assignee}</p>
    </div>
  );
}
