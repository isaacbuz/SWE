/**
 * Simple Tool Call Example
 *
 * Demonstrates basic tool calling with a single tool execution.
 */

import { ToolCallingPipeline } from "@ai-company/tool-pipeline";
import { ToolRegistry, ToolExecutor } from "@ai-company/openapi-tools";

// Mock LLM Provider
class SimpleLLMProvider {
  name = "simple-provider";

  async complete(messages: any[], tools: any[]) {
    // Simulate LLM response with tool call
    return {
      content: "I'll create that issue for you.",
      toolCalls: [
        {
          name: "createIssues",
          arguments: {
            owner: "isaacbuz",
            repo: "SWE",
            tasks: [
              {
                title: "Example Issue",
                body: "This is an example issue created via tool calling.",
              },
            ],
          },
        },
      ],
    };
  }
}

async function main() {
  // 1. Setup registry
  const registry = new ToolRegistry();
  await registry.loadSpecs(["./tools/openapi/ai-dev-tools.yaml"]);

  // 2. Setup executor
  const executor = new ToolExecutor();

  // Register tool handler
  executor.registerTool("createIssues", async (args) => {
    console.log("Creating issues:", args);
    // In production, call GitHub API here
    return {
      success: true,
      created: 1,
      issues: [
        { number: 123, url: "https://github.com/isaacbuz/SWE/issues/123" },
      ],
    };
  });

  // 3. Create pipeline
  const pipeline = new ToolCallingPipeline(
    registry,
    executor,
    new SimpleLLMProvider(),
  );

  // 4. Execute
  const result = await pipeline.execute(
    "Create a GitHub issue for the openapi-tools project",
  );

  console.log("Final Response:", result.finalResponse);
  console.log("Tool Results:", result.toolResults);
  console.log("Turns:", result.turns);
}

main().catch(console.error);
