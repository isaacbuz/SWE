/**
 * Tool Calling Pipeline
 * 
 * Orchestrates multi-turn tool calling between LLM providers and OpenAPI tools.
 * Handles tool discovery, conversion, execution, and result integration.
 */

import {
  ToolRegistry,
  ToolSpec,
  openApiToToolSpecs,
} from "@ai-company/openapi-tools";
import {
  ToolExecutor,
  ToolHandler,
  ToolResult as ExecutorResult,
} from "@ai-company/openapi-tools/executor";
import {
  ToolCall,
  ToolResult,
  LLMMessage,
  LLMCompletion,
  ToolCallingOptions,
  ToolCallingContext,
} from "./types.js";

export interface LLMProvider {
  /** Provider name */
  name: string;
  
  /** Generate completion with tool support */
  complete(
    messages: LLMMessage[],
    tools: ToolSpec[],
    systemPrompt?: string,
    options?: Record<string, unknown>
  ): Promise<LLMCompletion>;
}

export class ToolCallingPipeline {
  private toolRegistry: ToolRegistry;
  private toolExecutor: ToolExecutor;
  private llmProvider: LLMProvider;
  private options: Required<ToolCallingOptions>;

  constructor(
    toolRegistry: ToolRegistry,
    toolExecutor: ToolExecutor,
    llmProvider: LLMProvider,
    options: ToolCallingOptions = {}
  ) {
    this.toolRegistry = toolRegistry;
    this.toolExecutor = toolExecutor;
    this.llmProvider = llmProvider;
    this.options = {
      maxTurns: options.maxTurns ?? 10,
      stopOnFirstToolCall: options.stopOnFirstToolCall ?? false,
      timeoutPerTurn: options.timeoutPerTurn ?? 30000,
      validateResults: options.validateResults ?? true,
    };
  }

  /**
   * Execute a tool calling conversation
   */
  async execute(
    userMessage: string,
    systemPrompt?: string,
    availableTools?: string[]
  ): Promise<{
    finalResponse: string;
    toolResults: ToolResult[];
    turns: number;
    totalExecutionTimeMs: number;
  }> {
    const startTime = Date.now();
    const context: ToolCallingContext = {
      messages: [
        {
          role: "user",
          content: userMessage,
        },
      ],
      systemPrompt,
      toolResults: [],
      turn: 0,
    };

    // Get available tools
    const toolSpecs = this.getAvailableTools(availableTools);

    // Convert to LLM format
    const llmTools = this.convertToolsToLLMFormat(toolSpecs);

    // Multi-turn tool calling loop
    while (context.turn < this.options.maxTurns) {
      context.turn++;

      // Generate LLM response
      const completion = await this.llmProvider.complete(
        context.messages,
        toolSpecs,
        context.systemPrompt
      );

      // Add assistant message
      context.messages.push({
        role: "assistant",
        content: completion.content,
        toolCalls: completion.toolCalls,
      });

      // If no tool calls, we're done
      if (!completion.toolCalls || completion.toolCalls.length === 0) {
        break;
      }

      // Execute tool calls
      const toolResults = await this.executeToolCalls(
        completion.toolCalls,
        toolSpecs
      );

      // Add tool results to context
      context.toolResults.push(...toolResults);

      // Add tool result messages
      for (const result of toolResults) {
        context.messages.push({
          role: "tool",
          content: JSON.stringify(result.result),
          toolCallId: result.callId,
        });
      }

      // Stop if configured to stop on first tool call
      if (this.options.stopOnFirstToolCall) {
        break;
      }
    }

    // Get final response (last assistant message)
    const finalResponse =
      context.messages
        .filter((m) => m.role === "assistant")
        .pop()?.content || "";

    return {
      finalResponse,
      toolResults: context.toolResults,
      turns: context.turn,
      totalExecutionTimeMs: Date.now() - startTime,
    };
  }

  /**
   * Get available tools from registry
   */
  private getAvailableTools(toolNames?: string[]): ToolSpec[] {
    if (toolNames && toolNames.length > 0) {
      // Get specific tools
      return toolNames
        .map((name) => this.toolRegistry.getToolByName(name))
        .filter((tool): tool is ToolSpec => tool !== undefined);
    }

    // Get all tools
    return this.toolRegistry.getToolSpecs();
  }

  /**
   * Convert tool specs to LLM provider format
   */
  private convertToolsToLLMFormat(toolSpecs: ToolSpec[]): unknown[] {
    // Convert to OpenAI/Anthropic format
    return toolSpecs.map((tool) => ({
      type: "function",
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.jsonSchema,
      },
    }));
  }

  /**
   * Execute multiple tool calls
   */
  private async executeToolCalls(
    toolCalls: ToolCall[],
    toolSpecs: ToolSpec[]
  ): Promise<ToolResult[]> {
    const results: ToolResult[] = [];

    // Execute in parallel
    const executions = toolCalls.map((call) =>
      this.executeToolCall(call, toolSpecs)
    );

    const executorResults = await Promise.allSettled(executions);

    for (let i = 0; i < executorResults.length; i++) {
      const result = executorResults[i];
      const call = toolCalls[i];

      if (result.status === "fulfilled") {
        results.push(result.value);
      } else {
        results.push({
          name: call.name,
          result: null,
          success: false,
          error: result.reason?.message || "Unknown error",
          executionTimeMs: 0,
          callId: call.id,
        });
      }
    }

    return results;
  }

  /**
   * Execute a single tool call
   */
  private async executeToolCall(
    toolCall: ToolCall,
    toolSpecs: ToolSpec[]
  ): Promise<ToolResult> {
    const startTime = Date.now();

    // Find tool spec
    const toolSpec = toolSpecs.find((t) => t.name === toolCall.name);
    if (!toolSpec) {
      throw new Error(`Tool '${toolCall.name}' not found`);
    }

    // Execute tool
    const executorResult: ExecutorResult = await this.toolExecutor.execute(
      toolCall.name,
      toolCall.arguments,
      toolSpec
    );

    return {
      name: toolCall.name,
      result: executorResult.result,
      success: executorResult.success,
      error: executorResult.error,
      executionTimeMs: executorResult.executionTimeMs,
      callId: toolCall.id,
    };
  }

  /**
   * Register a tool handler
   */
  registerToolHandler(
    toolName: string,
    handler: ToolHandler,
    spec?: ToolSpec
  ): void {
    this.toolExecutor.registerTool(toolName, handler, spec);
  }

  /**
   * Get pipeline statistics
   */
  getStats(): {
    availableTools: number;
    registeredHandlers: number;
  } {
    return {
      availableTools: this.toolRegistry.getToolCount(),
      registeredHandlers: this.toolExecutor.getRegisteredTools().length,
    };
  }
}

