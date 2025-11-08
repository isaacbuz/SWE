import { Bot, Plus, Search, Sparkles } from "lucide-react";

const agents = [
  {
    id: "1",
    name: "Chief Architect",
    role: "System Design",
    status: "active",
    skills: ["Architecture", "System Design", "Planning"],
    tasksCompleted: 156,
    successRate: 94,
  },
  {
    id: "2",
    name: "Codegen Agent",
    role: "Code Generation",
    status: "active",
    skills: ["TypeScript", "React", "Node.js"],
    tasksCompleted: 234,
    successRate: 91,
  },
  {
    id: "3",
    name: "Code Review Agent",
    role: "Code Review",
    status: "idle",
    skills: ["Quality Assurance", "Best Practices", "Security"],
    tasksCompleted: 189,
    successRate: 96,
  },
  {
    id: "4",
    name: "DevOps Agent",
    role: "Infrastructure",
    status: "active",
    skills: ["Docker", "Kubernetes", "CI/CD"],
    tasksCompleted: 127,
    successRate: 88,
  },
];

export default function AgentsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink-primary">Agent Roster</h1>
          <p className="mt-2 text-ink-secondary">Manage your AI agent workforce</p>
        </div>
        <button className="flex items-center gap-2 rounded-md bg-brand-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-hover">
          <Sparkles className="h-4 w-4" />
          Compose Crew
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-tertiary" />
          <input
            type="text"
            placeholder="Search agents..."
            className="w-full rounded-md border border-border-default bg-surface-secondary py-2 pl-10 pr-4 text-sm text-ink-primary placeholder:text-ink-tertiary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
          />
        </div>
        <select className="rounded-md border border-border-default bg-surface-secondary px-4 py-2 text-sm text-ink-primary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary">
          <option>All Status</option>
          <option>Active</option>
          <option>Idle</option>
          <option>Offline</option>
        </select>
      </div>

      {/* Agents Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
        
        {/* Add New Agent Card */}
        <button className="group flex min-h-[280px] flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed border-border-default bg-surface-secondary transition-all hover:border-brand-primary hover:bg-brand-primary/5">
          <div className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-dashed border-border-default bg-surface-primary group-hover:border-brand-primary group-hover:bg-brand-primary/10">
            <Plus className="h-8 w-8 text-ink-tertiary group-hover:text-brand-primary" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-ink-primary group-hover:text-brand-primary">Add New Agent</p>
            <p className="mt-1 text-xs text-ink-tertiary">Configure a specialized agent</p>
          </div>
        </button>
      </div>
    </div>
  );
}

function AgentCard({ agent }: { agent: typeof agents[0] }) {
  const statusColors = {
    active: "bg-status-success/10 text-status-success border-status-success/20",
    idle: "bg-ink-disabled/10 text-ink-disabled border-ink-disabled/20",
    offline: "bg-ink-disabled/10 text-ink-disabled border-ink-disabled/20",
  };

  return (
    <div className="group rounded-lg border border-border-default bg-surface-secondary p-6 transition-all hover:border-brand-primary hover:shadow-e2">
      <div className="flex items-start justify-between">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-primary/10">
          <Bot className="h-6 w-6 text-brand-primary" />
        </div>
        <span className={"rounded-full border px-2 py-1 text-xs font-medium " + statusColors[agent.status as keyof typeof statusColors]}>
          {agent.status}
        </span>
      </div>
      
      <h3 className="mt-4 text-lg font-semibold text-ink-primary">
        {agent.name}
      </h3>
      <p className="mt-1 text-sm text-ink-secondary">
        {agent.role}
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {agent.skills.slice(0, 3).map((skill) => (
          <span
            key={skill}
            className="rounded-md bg-surface-tertiary px-2 py-1 text-xs text-ink-secondary"
          >
            {skill}
          </span>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 border-t border-border-subtle pt-4">
        <div>
          <p className="text-xs text-ink-tertiary">Tasks</p>
          <p className="mt-1 text-lg font-semibold text-ink-primary">{agent.tasksCompleted}</p>
        </div>
        <div>
          <p className="text-xs text-ink-tertiary">Success Rate</p>
          <p className="mt-1 text-lg font-semibold text-status-success">{agent.successRate}%</p>
        </div>
      </div>
    </div>
  );
}
