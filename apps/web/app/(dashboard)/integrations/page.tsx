import { Check, ExternalLink, Plus } from "lucide-react";

const integrations = [
  {
    id: "1",
    name: "GitHub",
    description: "Connect your repositories for automated PR reviews and deployments",
    connected: true,
    icon: "🐙",
  },
  {
    id: "2",
    name: "Jira",
    description: "Sync issues and project boards with your workflow",
    connected: true,
    icon: "📋",
  },
  {
    id: "3",
    name: "Slack",
    description: "Get notifications and interact with agents via Slack",
    connected: false,
    icon: "💬",
  },
  {
    id: "4",
    name: "Linear",
    description: "Integrate with Linear for seamless issue tracking",
    connected: false,
    icon: "⚡",
  },
  {
    id: "5",
    name: "AWS",
    description: "Deploy and manage infrastructure on AWS",
    connected: true,
    icon: "☁️",
  },
  {
    id: "6",
    name: "Vercel",
    description: "Automated deployments to Vercel",
    connected: false,
    icon: "▲",
  },
];

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink-primary">Integrations</h1>
          <p className="mt-2 text-ink-secondary">Connect external services and tools</p>
        </div>
        <button className="flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-tertiary transition-colors">
          <Plus className="h-4 w-4" />
          Request Integration
        </button>
      </div>

      {/* Connected Integrations */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-ink-primary">Connected</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {integrations
            .filter((i) => i.connected)
            .map((integration) => (
              <IntegrationCard key={integration.id} integration={integration} />
            ))}
        </div>
      </div>

      {/* Available Integrations */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-ink-primary">Available</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {integrations
            .filter((i) => !i.connected)
            .map((integration) => (
              <IntegrationCard key={integration.id} integration={integration} />
            ))}
        </div>
      </div>
    </div>
  );
}

function IntegrationCard({ integration }: { integration: typeof integrations[0] }) {
  return (
    <div className="group rounded-lg border border-border-default bg-surface-secondary p-6 transition-all hover:border-brand-primary hover:shadow-e2">
      <div className="flex items-start justify-between">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-surface-tertiary text-2xl">
          {integration.icon}
        </div>
        {integration.connected ? (
          <span className="flex items-center gap-1 rounded-full border border-status-success/20 bg-status-success/10 px-2 py-1 text-xs font-medium text-status-success">
            <Check className="h-3 w-3" />
            Connected
          </span>
        ) : (
          <button className="rounded-md bg-brand-primary px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-brand-hover">
            Connect
          </button>
        )}
      </div>

      <h3 className="mt-4 text-lg font-semibold text-ink-primary">{integration.name}</h3>
      <p className="mt-2 text-sm text-ink-secondary">{integration.description}</p>

      {integration.connected && (
        <div className="mt-4 flex items-center gap-2 border-t border-border-subtle pt-4">
          <button className="flex items-center gap-1 text-sm text-brand-primary hover:underline">
            <span>Configure</span>
            <ExternalLink className="h-3 w-3" />
          </button>
          <span className="text-ink-tertiary">•</span>
          <button className="text-sm text-status-danger hover:underline">
            Disconnect
          </button>
        </div>
      )}
    </div>
  );
}
