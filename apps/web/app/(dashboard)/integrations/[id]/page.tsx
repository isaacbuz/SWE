"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { ArrowLeft, Check, X, AlertCircle, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

interface IntegrationDetailProps {
  params: {
    id: string;
  };
}

// Mock integration details
const integrationDetails: Record<string, any> = {
  github: {
    name: "GitHub",
    description:
      "Connect your GitHub repositories for seamless code management",
    status: "connected",
    config: {
      organization: "my-company",
      repository: "my-repo",
      branch: "main",
      webhookUrl: "https://api.example.com/webhooks/github",
    },
  },
  anthropic: {
    name: "Anthropic",
    description: "Access Claude AI models for code generation and analysis",
    status: "connected",
    config: {
      apiKey: "sk-ant-api03-***************",
      model: "claude-sonnet-4-5",
      maxTokens: 4096,
    },
  },
  openai: {
    name: "OpenAI",
    description: "Integrate GPT models for AI assistance",
    status: "connected",
    config: {
      apiKey: "sk-***************",
      model: "gpt-5",
      maxTokens: 4096,
      temperature: 0.7,
    },
  },
};

export default function IntegrationDetailPage({
  params,
}: IntegrationDetailProps) {
  const integration = integrationDetails[params.id];
  const [isEditing, setIsEditing] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<"success" | "error" | null>(
    null,
  );

  if (!integration) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Integration Not Found</h2>
          <p className="text-muted-foreground mb-4">
            The requested integration does not exist.
          </p>
          <Link href="/integrations">
            <Button>Back to Integrations</Button>
          </Link>
        </div>
      </div>
    );
  }

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    // Simulate API call
    setTimeout(() => {
      setTestResult("success");
      setIsTesting(false);
    }, 2000);
  };

  const handleSave = () => {
    setIsEditing(false);
    // Save logic here
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/integrations"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Integrations
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {integration.name}
            </h1>
            <p className="text-muted-foreground">{integration.description}</p>
          </div>
          <Badge
            variant={integration.status === "connected" ? "success" : "outline"}
          >
            {integration.status}
          </Badge>
        </div>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Manage your integration settings</CardDescription>
          </div>
          {!isEditing ? (
            <Button onClick={() => setIsEditing(true)}>Edit</Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave}>Save Changes</Button>
            </div>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {params.id === "github" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="organization">Organization</Label>
                <Input
                  id="organization"
                  defaultValue={integration.config.organization}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="repository">Repository</Label>
                <Input
                  id="repository"
                  defaultValue={integration.config.repository}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="branch">Default Branch</Label>
                <Input
                  id="branch"
                  defaultValue={integration.config.branch}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="webhook">Webhook URL</Label>
                <Input
                  id="webhook"
                  defaultValue={integration.config.webhookUrl}
                  disabled={!isEditing}
                />
              </div>
            </>
          )}

          {params.id === "anthropic" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="apiKey">API Key</Label>
                <Input
                  id="apiKey"
                  type="password"
                  defaultValue={integration.config.apiKey}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="model">Model</Label>
                <Select
                  id="model"
                  defaultValue={integration.config.model}
                  disabled={!isEditing}
                >
                  <option value="claude-sonnet-4-5">Claude Sonnet 4.5</option>
                  <option value="claude-opus-4">Claude Opus 4</option>
                  <option value="claude-haiku-3-5">Claude Haiku 3.5</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxTokens">Max Tokens</Label>
                <Input
                  id="maxTokens"
                  type="number"
                  defaultValue={integration.config.maxTokens}
                  disabled={!isEditing}
                />
              </div>
            </>
          )}

          {params.id === "openai" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="apiKey">API Key</Label>
                <Input
                  id="apiKey"
                  type="password"
                  defaultValue={integration.config.apiKey}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="model">Model</Label>
                <Select
                  id="model"
                  defaultValue={integration.config.model}
                  disabled={!isEditing}
                >
                  <option value="gpt-5">GPT-5</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxTokens">Max Tokens</Label>
                <Input
                  id="maxTokens"
                  type="number"
                  defaultValue={integration.config.maxTokens}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  defaultValue={integration.config.temperature}
                  disabled={!isEditing}
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Test Connection */}
      <Card>
        <CardHeader>
          <CardTitle>Test Connection</CardTitle>
          <CardDescription>
            Verify that your integration is working correctly
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={handleTestConnection}
            disabled={isTesting}
            className="w-full sm:w-auto"
          >
            {isTesting ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              <>Test Connection</>
            )}
          </Button>

          {testResult === "success" && (
            <div className="flex items-center gap-2 text-green-600">
              <Check className="h-5 w-5" />
              <span>Connection successful!</span>
            </div>
          )}

          {testResult === "error" && (
            <div className="flex items-center gap-2 text-red-600">
              <X className="h-5 w-5" />
              <span>Connection failed. Please check your configuration.</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>
            Irreversible actions for this integration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="destructive">Disconnect Integration</Button>
        </CardContent>
      </Card>
    </div>
  );
}
