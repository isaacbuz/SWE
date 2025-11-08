import { FolderKanban, Plus, Search } from "lucide-react";
import Link from "next/link";

const projects = [
  {
    id: "1",
    name: "E-Commerce Platform",
    description: "Full-stack e-commerce solution with payment integration",
    status: "active",
    specs: 12,
    prs: 5,
    agents: 3,
  },
  {
    id: "2",
    name: "Mobile App Refactor",
    description: "React Native to Flutter migration",
    status: "active",
    specs: 8,
    prs: 2,
    agents: 2,
  },
  {
    id: "3",
    name: "API Gateway",
    description: "Microservices API gateway implementation",
    status: "planning",
    specs: 15,
    prs: 0,
    agents: 1,
  },
];

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink-primary">Projects</h1>
          <p className="mt-2 text-ink-secondary">Manage your AI-powered development projects</p>
        </div>
        <button className="flex items-center gap-2 rounded-md bg-brand-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-hover">
          <Plus className="h-4 w-4" />
          New Project
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-tertiary" />
          <input
            type="text"
            placeholder="Search projects..."
            className="w-full rounded-md border border-border-default bg-surface-secondary py-2 pl-10 pr-4 text-sm text-ink-primary placeholder:text-ink-tertiary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
          />
        </div>
        <select className="rounded-md border border-border-default bg-surface-secondary px-4 py-2 text-sm text-ink-primary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary">
          <option>All Status</option>
          <option>Active</option>
          <option>Planning</option>
          <option>Archived</option>
        </select>
      </div>

      {/* Projects Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
}

function ProjectCard({ project }: { project: typeof projects[0] }) {
  const statusColors = {
    active: "bg-status-success/10 text-status-success border-status-success/20",
    planning: "bg-status-warning/10 text-status-warning border-status-warning/20",
    archived: "bg-ink-disabled/10 text-ink-disabled border-ink-disabled/20",
  };

  return (
    <Link
      href={"/projects/" + project.id}
      className="group rounded-lg border border-border-default bg-surface-secondary p-6 transition-all hover:border-brand-primary hover:shadow-e2"
    >
      <div className="flex items-start justify-between">
        <FolderKanban className="h-8 w-8 text-brand-primary" />
        <span className={"rounded-full border px-2 py-1 text-xs font-medium " + statusColors[project.status as keyof typeof statusColors]}>
          {project.status}
        </span>
      </div>
      
      <h3 className="mt-4 text-lg font-semibold text-ink-primary group-hover:text-brand-primary transition-colors">
        {project.name}
      </h3>
      <p className="mt-2 text-sm text-ink-secondary line-clamp-2">
        {project.description}
      </p>

      <div className="mt-6 flex items-center gap-4 text-xs text-ink-tertiary">
        <span>{project.specs} specs</span>
        <span>•</span>
        <span>{project.prs} PRs</span>
        <span>•</span>
        <span>{project.agents} agents</span>
      </div>
    </Link>
  );
}
