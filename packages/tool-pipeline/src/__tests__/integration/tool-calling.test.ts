/**
 * Integration Tests for Tool Calling Pipeline
 */

import { describe, it, expect, beforeEach } from "vitest";
import { ToolCallingPipeline } from "../../ToolCallingPipeline.js";
import { ToolRegistry } from "@ai-company/openapi-tools";
import { ToolExecutor } from "@ai-company/openapi-tools/executor";
import type { LLMProvider, LLMCompletion, LLMMessage } from "../../ToolCallingPipeline.js";
import type { ToolCall } from "../../types.js";

/**
 * Mock LLM Provider for testing
 */
class MockLLMProvider implements LLMProvider {
  name = "mock-provider";
  private responses: LLMCompletion[] = [];
  private currentIndex = 0;

  setResponse(response: LLMCompletion): void {
    this.responses = [response];
    this.currentIndex = 0;
  }

  setResponseSequence(responses: LLMCompletion[]): void {
    this.responses = responses;
    this.currentIndex = 0;
  }

  async complete(
    messages: LLMMessage[],
    tools: unknown[],
    systemPrompt?: string
  ): Promise<LLMCompletion> {
    if (this.currentIndex >= this.responses.length) {
      throw new Error("No more responses configured");
    }

    const response = this.responses[this.currentIndex];
    this.currentIndex++;
    return response;
  }
}

describe("Tool Calling Pipeline Integration", () => {
  let pipeline: ToolCallingPipeline;
  let mockProvider: MockLLMProvider;
  let toolRegistry: ToolRegistry;
  let toolExecutor: ToolExecutor;

  beforeEach(async () => {
    mockProvider = new MockLLMProvider();
    toolRegistry = new ToolRegistry();
    toolExecutor = new ToolExecutor({ checkPermissions: false });

    // Load test OpenAPI spec
    await toolRegistry.loadSpecs([
      {
        openapi: "3.1.0",
        info: { title: "Test API", version: "1.0.0" },
        paths: {
          "/test/create": {
            post: {
              operationId: "createTest",
              summary: "Create test item",
              requestBody: {
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["name"],
                      properties: {
                        name: { type: "string" },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    ]);

    // Register tool handler
    toolExecutor.registerTool("createTest", async (args) => {
      return {
        success: true,
        id: "test-123",
        name: args.name as string,
      };
    });

    pipeline = new ToolCallingPipeline(
      toolRegistry,
      toolExecutor,
      mockProvider,
      {
        maxTurns: 10,
        timeoutPerTurn: 5000,
      }
    );
  });

  describe("Single Tool Call", () => {
    it("should execute tool and return result", async () => {
      // Mock LLM response with tool call
      mockProvider.setResponse({
        content: "I'll create a test item for you.",
        toolCalls: [
          {
            name: "createTest",
            arguments: {
              name: "Test Item",
            },
            id: "call_123",
          },
        ],
      });

      const result = await pipeline.execute(
        "Create a test item named 'Test Item'"
      );

      expect(result.finalResponse).toContain("Test Item");
      expect(result.toolResults).toHaveLength(1);
      expect(result.toolResults[0].name).toBe("createTest");
      expect(result.toolResults[0].success).toBe(true);
      expect(result.turns).toBe(1);
    });

    it("should handle invalid tool arguments", async () => {
      mockProvider.setResponse({
        content: "",
        toolCalls: [
          {
            name: "createTest",
            arguments: {}, // Missing required 'name' field
            id: "call_123",
          },
        ],
      });

      const result = await pipeline.execute("Create test");

      expect(result.toolResults).toHaveLength(1);
      expect(result.toolResults[0].success).toBe(false);
      expect(result.toolResults[0].error).toBeDefined();
    });

    it("should handle tool execution failure", async () => {
      // Register failing handler
      toolExecutor.registerTool("createTest", async () => {
        throw new Error("Tool execution failed");
      });

      mockProvider.setResponse({
        content: "",
        toolCalls: [
          {
            name: "createTest",
            arguments: { name: "Test" },
            id: "call_123",
          },
        ],
      });

      const result = await pipeline.execute("Create test");

      expect(result.toolResults).toHaveLength(1);
      expect(result.toolResults[0].success).toBe(false);
      expect(result.toolResults[0].error).toContain("failed");
    });
  });

  describe("Multi-Turn Tool Calling", () => {
    it("should handle multiple tool calls in sequence", async () => {
      // First turn: LLM calls tool
      mockProvider.setResponseSequence([
        {
          content: "",
          toolCalls: [
            {
              name: "createTest",
              arguments: { name: "Item 1" },
              id: "call_1",
            },
          ],
        },
        {
          content: "Created Item 1. Now creating Item 2.",
          toolCalls: [
            {
              name: "createTest",
              arguments: { name: "Item 2" },
              id: "call_2",
            },
          ],
        },
        {
          content: "Successfully created both items.",
        },
      ]);

      const result = await pipeline.execute("Create two test items");

      expect(result.toolResults).toHaveLength(2);
      expect(result.turns).toBe(3);
      expect(result.finalResponse).toContain("Successfully created");
    });

    it("should respect max turns limit", async () => {
      // Create infinite loop scenario
      mockProvider.setResponse({
        content: "",
        toolCalls: [
          {
            name: "createTest",
            arguments: { name: "Test" },
            id: "call_1",
          },
        ],
      });

      const limitedPipeline = new ToolCallingPipeline(
        toolRegistry,
        toolExecutor,
        mockProvider,
        {
          maxTurns: 2,
        }
      );

      const result = await limitedPipeline.execute("Create test");

      expect(result.turns).toBeLessThanOrEqual(2);
    });
  });

  describe("Error Handling", () => {
    it("should handle tool not found error", async () => {
      mockProvider.setResponse({
        content: "",
        toolCalls: [
          {
            name: "nonexistentTool",
            arguments: {},
            id: "call_123",
          },
        ],
      });

      const result = await pipeline.execute("Call nonexistent tool");

      expect(result.toolResults).toHaveLength(1);
      expect(result.toolResults[0].success).toBe(false);
      expect(result.toolResults[0].error).toContain("not found");
    });

    it("should handle LLM provider errors gracefully", async () => {
      const errorProvider: LLMProvider = {
        name: "error-provider",
        async complete() {
          throw new Error("LLM provider error");
        },
      };

      const errorPipeline = new ToolCallingPipeline(
        toolRegistry,
        toolExecutor,
        errorProvider
      );

      await expect(
        errorPipeline.execute("Test")
      ).rejects.toThrow("LLM provider error");
    });
  });

  describe("Pipeline Statistics", () => {
    it("should return correct statistics", () => {
      const stats = pipeline.getStats();

      expect(stats.availableTools).toBeGreaterThan(0);
      expect(stats.registeredHandlers).toBeGreaterThan(0);
    });
  });
});

