"use client";

import { useState, useEffect } from "react";
import { Check, ExternalLink, Plus } from "lucide-react";
import { IntegrationDetail } from "@/components/integrations/integration-detail";

interface Integration {
  id: string;
  name: string;
  description: string;
  connected: boolean;
  icon: string;
  status?: "connected" | "disconnected" | "error";
  health?: "healthy" | "degraded" | "down";
  rateLimit?: {
    remaining: number;
    limit: number;
    resetAt?: Date;
  };
  credentials?: {
    masked: string;
    lastUpdated?: Date;
  };
  tools?: Array<{
    id: string;
    name: string;
    enabled: boolean;
    description?: string;
  }>;
  usage?: {
    last7Days: number;
    last30Days: number;
  };
}

const integrations: Integration[] = [
  {
    id: "1",
    name: "GitHub",
    description:
      "Connect your repositories for automated PR reviews and deployments",
    connected: true,
    icon: "🐙",
    status: "connected",
    health: "healthy",
    rateLimit: {
      remaining: 4823,
      limit: 5000,
      resetAt: new Date(Date.now() + 42 * 60 * 1000),
    },
    credentials: {
      masked: "ghp_••••••••••••••••",
      lastUpdated: new Date(),
    },
    tools: [
      {
        id: "createIssues",
        name: "Create Issues",
        enabled: true,
        description: "Create GitHub issues",
      },
      {
        id: "createPR",
        name: "Create Pull Requests",
        enabled: true,
        description: "Create pull requests",
      },
      {
        id: "reviewPR",
        name: "Review PRs",
        enabled: true,
        description: "Review pull requests",
      },
      {
        id: "updateIssues",
        name: "Update Issues",
        enabled: true,
        description: "Update issue status",
      },
      {
        id: "mergePR",
        name: "Merge PRs",
        enabled: true,
        description: "Merge pull requests",
      },
      {
        id: "deleteBranches",
        name: "Delete Branches",
        enabled: false,
        description: "Delete branches (disabled)",
      },
    ],
    usage: {
      last7Days: 234,
      last30Days: 892,
    },
  },
  {
    id: "2",
    name: "GSA (Open GSA)",
    description: "Search federal grants and contracts",
    connected: true,
    icon: "🏛️",
    status: "connected",
    health: "healthy",
    credentials: {
      masked: "••••••••••••••••",
      lastUpdated: new Date(),
    },
    tools: [
      {
        id: "searchEntities",
        name: "Search Entities",
        enabled: true,
        description: "Search federal entities",
      },
      {
        id: "searchContracts",
        name: "Search Contracts",
        enabled: true,
        description: "Search contracts",
      },
      {
        id: "getHierarchy",
        name: "Get Federal Hierarchy",
        enabled: true,
        description: "Get federal hierarchy",
      },
    ],
    usage: {
      last7Days: 12,
      last30Days: 45,
    },
  },
  {
    id: "3",
    name: "Vercel",
    description: "Automated deployments to Vercel",
    connected: false,
    icon: "▲",
    status: "disconnected",
    health: "down",
    tools: [],
  },
];

export default function IntegrationsPage() {
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(
    null,
  );

  const handleTestConnection = async (id: string) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      success: true,
      message: "Connection test successful. All checks passed!",
    };
  };

  const handleUpdateCredentials = async (
    id: string,
    credentials: Record<string, string>,
  ) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 500));
    console.log("Updating credentials for", id);
  };

  const handleToggleTool = async (
    integrationId: string,
    toolId: string,
    enabled: boolean,
  ) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 300));
    console.log("Toggling tool", toolId, "to", enabled);
  };

  const selected = integrations.find((i) => i.id === selectedIntegration);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink-primary">Integrations</h1>
          <p className="mt-2 text-ink-secondary">
            Manage API credentials, view tool health, and configure permissions
          </p>
        </div>
        <button className="flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-tertiary transition-colors">
          <Plus className="h-4 w-4" />
          Add Integration
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Integrations List */}
        <div className="lg:col-span-1 space-y-4">
          {integrations.map((integration) => (
            <div
              key={integration.id}
              onClick={() => setSelectedIntegration(integration.id)}
              className={`
                cursor-pointer rounded-lg border p-4 transition-all
                ${
                  selectedIntegration === integration.id
                    ? "border-brand-primary bg-blue-50"
                    : "border-border-subtle bg-surface-secondary hover:border-border-default"
                }
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">{integration.icon}</div>
                  <div>
                    <div className="font-semibold text-ink-primary">
                      {integration.name}
                    </div>
                    <div className="text-sm text-ink-tertiary">
                      {integration.status === "connected"
                        ? "🟢 Connected"
                        : "🔴 Not Connected"}
                    </div>
                  </div>
                </div>
                {integration.connected && (
                  <Check className="h-5 w-5 text-green-500" />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Integration Detail */}
        <div className="lg:col-span-2">
          {selected ? (
            <IntegrationDetail
              integration={selected}
              onTestConnection={handleTestConnection}
              onUpdateCredentials={handleUpdateCredentials}
              onToggleTool={handleToggleTool}
            />
          ) : (
            <div className="rounded-lg border border-border-subtle bg-surface-secondary p-12 text-center">
              <p className="text-ink-tertiary">
                Select an integration to view details and manage settings
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function IntegrationCard({
  integration,
}: {
  integration: (typeof integrations)[0];
}) {
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

      <h3 className="mt-4 text-lg font-semibold text-ink-primary">
        {integration.name}
      </h3>
      <p className="mt-2 text-sm text-ink-secondary">
        {integration.description}
      </p>

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
