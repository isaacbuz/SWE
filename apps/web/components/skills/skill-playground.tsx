"use client";

import { useState } from "react";
import { Play, Loader2, CheckCircle2, XCircle, Zap } from "lucide-react";
import { useExecuteSkill } from "@/lib/hooks/use-skills";
import { SkillDetail, SkillExecutionResult } from "@/lib/api/skills";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface SkillPlaygroundProps {
  skill: SkillDetail;
}

export function SkillPlayground({ skill }: SkillPlaygroundProps) {
  const [inputs, setInputs] = useState<Record<string, any>>({});
  const [result, setResult] = useState<SkillExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const executeSkill = useExecuteSkill();

  // Initialize inputs from schema
  const initializeInputs = () => {
    const initial: Record<string, any> = {};
    if (skill.input_schema?.properties) {
      Object.keys(skill.input_schema.properties).forEach((key) => {
        const prop = skill.input_schema.properties[key];
        if (prop.default !== undefined) {
          initial[key] = prop.default;
        } else if (prop.type === "string") {
          initial[key] = "";
        } else if (prop.type === "number") {
          initial[key] = 0;
        } else if (prop.type === "boolean") {
          initial[key] = false;
        } else if (prop.type === "array") {
          initial[key] = [];
        } else if (prop.type === "object") {
          initial[key] = {};
        }
      });
    }
    setInputs(initial);
  };

  const handleExecute = async () => {
    setError(null);
    setResult(null);

    try {
      const executionResult = await executeSkill.mutateAsync({
        skillId: skill.id,
        request: {
          skill_id: skill.id,
          inputs,
          context: {},
        },
      });
      setResult(executionResult);
    } catch (err: any) {
      setError(err.message || "Failed to execute skill");
    }
  };

  const updateInput = (key: string, value: any) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
  };

  // Render input field based on schema type
  const renderInput = (key: string, prop: any) => {
    const value = inputs[key] ?? "";
    const isRequired = skill.input_schema?.required?.includes(key);

    if (prop.type === "string" && prop.format === "textarea") {
      return (
        <div key={key} className="space-y-2">
          <label className="text-sm font-medium text-ink-primary">
            {prop.title || key}
            {isRequired && <span className="text-status-error">*</span>}
          </label>
          <textarea
            value={value}
            onChange={(e) => updateInput(key, e.target.value)}
            placeholder={prop.placeholder || prop.description}
            className="w-full rounded-md border border-border-default bg-surface-secondary px-3 py-2 text-sm text-ink-primary placeholder:text-ink-tertiary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
            rows={4}
          />
          {prop.description && (
            <p className="text-xs text-ink-tertiary">{prop.description}</p>
          )}
        </div>
      );
    }

    if (prop.type === "string") {
      return (
        <div key={key} className="space-y-2">
          <label className="text-sm font-medium text-ink-primary">
            {prop.title || key}
            {isRequired && <span className="text-status-error">*</span>}
          </label>
          <input
            type="text"
            value={value}
            onChange={(e) => updateInput(key, e.target.value)}
            placeholder={prop.placeholder || prop.description}
            className="w-full rounded-md border border-border-default bg-surface-secondary px-3 py-2 text-sm text-ink-primary placeholder:text-ink-tertiary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
          />
          {prop.description && (
            <p className="text-xs text-ink-tertiary">{prop.description}</p>
          )}
        </div>
      );
    }

    if (prop.type === "number") {
      return (
        <div key={key} className="space-y-2">
          <label className="text-sm font-medium text-ink-primary">
            {prop.title || key}
            {isRequired && <span className="text-status-error">*</span>}
          </label>
          <input
            type="number"
            value={value}
            onChange={(e) => updateInput(key, Number(e.target.value))}
            placeholder={prop.placeholder || prop.description}
            className="w-full rounded-md border border-border-default bg-surface-secondary px-3 py-2 text-sm text-ink-primary placeholder:text-ink-tertiary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
          />
          {prop.description && (
            <p className="text-xs text-ink-tertiary">{prop.description}</p>
          )}
        </div>
      );
    }

    if (prop.type === "boolean") {
      return (
        <div key={key} className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => updateInput(key, e.target.checked)}
            className="h-4 w-4 rounded border-border-default text-brand-primary focus:ring-brand-primary"
          />
          <label className="text-sm font-medium text-ink-primary">
            {prop.title || key}
            {isRequired && <span className="text-status-error">*</span>}
          </label>
        </div>
      );
    }

    return (
      <div key={key} className="space-y-2">
        <label className="text-sm font-medium text-ink-primary">
          {prop.title || key}
          {isRequired && <span className="text-status-error">*</span>}
        </label>
        <textarea
          value={JSON.stringify(value, null, 2)}
          onChange={(e) => {
            try {
              updateInput(key, JSON.parse(e.target.value));
            } catch {
              // Invalid JSON, ignore
            }
          }}
          placeholder="Enter JSON"
          className="w-full rounded-md border border-border-default bg-surface-secondary px-3 py-2 font-mono text-sm text-ink-primary placeholder:text-ink-tertiary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
          rows={4}
        />
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card className="p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink-primary">Inputs</h3>
          <Button variant="outline" size="sm" onClick={initializeInputs}>
            Reset
          </Button>
        </div>

        <div className="space-y-4">
          {skill.input_schema?.properties ? (
            Object.entries(skill.input_schema.properties).map(
              ([key, prop]: [string, any]) => renderInput(key, prop),
            )
          ) : (
            <p className="text-sm text-ink-tertiary">No inputs required</p>
          )}
        </div>

        <div className="mt-6">
          <Button
            onClick={handleExecute}
            disabled={executeSkill.isPending}
            className="w-full"
          >
            {executeSkill.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Executing...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Execute Skill
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Results Section */}
      {error && (
        <Card className="border-status-error/20 bg-status-error/10 p-6">
          <div className="flex items-start gap-3">
            <XCircle className="h-5 w-5 text-status-error" />
            <div>
              <h3 className="font-semibold text-status-error">
                Execution Failed
              </h3>
              <p className="mt-1 text-sm text-status-error">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {result && (
        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {result.validation_passed ? (
                <CheckCircle2 className="h-5 w-5 text-status-success" />
              ) : (
                <XCircle className="h-5 w-5 text-status-error" />
              )}
              <h3 className="text-lg font-semibold text-ink-primary">
                Results
              </h3>
            </div>
            {result.cache_hit && (
              <span className="text-xs text-ink-tertiary">Cached</span>
            )}
          </div>

          {/* Output */}
          {result.outputs && (
            <div className="mb-4 space-y-2">
              <h4 className="text-sm font-medium text-ink-secondary">Output</h4>
              <pre className="overflow-auto rounded-md border border-border-default bg-surface-secondary p-4 text-sm">
                {JSON.stringify(result.outputs, null, 2)}
              </pre>
            </div>
          )}

          {/* Metrics */}
          <div className="grid grid-cols-2 gap-4 border-t border-border-default pt-4 sm:grid-cols-4">
            {result.latency_ms !== undefined && (
              <div>
                <p className="text-xs text-ink-tertiary">Latency</p>
                <p className="text-sm font-medium text-ink-primary">
                  {result.latency_ms}ms
                </p>
              </div>
            )}
            {result.tokens_input !== undefined && (
              <div>
                <p className="text-xs text-ink-tertiary">Input Tokens</p>
                <p className="text-sm font-medium text-ink-primary">
                  {result.tokens_input.toLocaleString()}
                </p>
              </div>
            )}
            {result.tokens_output !== undefined && (
              <div>
                <p className="text-xs text-ink-tertiary">Output Tokens</p>
                <p className="text-sm font-medium text-ink-primary">
                  {result.tokens_output.toLocaleString()}
                </p>
              </div>
            )}
            {result.cost_usd !== undefined && (
              <div>
                <p className="text-xs text-ink-tertiary">Cost</p>
                <p className="text-sm font-medium text-ink-primary">
                  ${result.cost_usd.toFixed(6)}
                </p>
              </div>
            )}
          </div>

          {/* Validation */}
          {result.validation_result && (
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-medium text-ink-secondary">
                Validation
              </h4>
              <div className="rounded-md border border-border-default bg-surface-secondary p-3">
                <p
                  className={`text-sm ${result.validation_passed ? "text-status-success" : "text-status-error"}`}
                >
                  {result.validation_passed
                    ? "✓ Validation passed"
                    : "✗ Validation failed"}
                </p>
                {result.validation_result.errors &&
                  result.validation_result.errors.length > 0 && (
                    <ul className="mt-2 list-disc list-inside text-sm text-status-error">
                      {result.validation_result.errors.map(
                        (err: string, i: number) => (
                          <li key={i}>{err}</li>
                        ),
                      )}
                    </ul>
                  )}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
