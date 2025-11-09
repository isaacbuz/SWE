/**
 * Tool Calling Pipeline
 * 
 * Orchestrates multi-turn tool calling between LLM providers and tools.
 */
import { ToolRegistry, ToolExecutor, ToolSpec } from '@ai-company/openapi-tools';
import { ToolCall, ToolCallResult, PipelineMessage, PipelineResult, PipelineOptions } from './types';

export interface LLMProvider {
  /** Generate completion with optional tools */
  complete(
    messages: PipelineMessage[],
    tools?: ToolSpec[],
    options?: {
      temperature?: number;
      maxTokens?: number;
      [key: string]: any;
    }
  ): Promise<{
    content: string;
    toolCalls?: ToolCall[];
    usage?: {
      inputTokens: number;
      outputTokens: number;
    };
    model?: string;
  }>;
}

export class ToolCallingPipeline {
  private registry: ToolRegistry;
  private executor: ToolExecutor;
  private provider: LLMProvider;
  private options: Required<PipelineOptions>;

  constructor(
    registry: ToolRegistry,
    executor: ToolExecutor,
    provider: LLMProvider,
    options: PipelineOptions = {}
  ) {
    this.registry = registry;
    this.executor = executor;
    this.provider = provider;
    this.options = {
      maxTurns: options.maxTurns ?? 5,
      verbose: options.verbose ?? false,
      onToolCall: options.onToolCall ?? (() => {}),
      onToolResult: options.onToolResult ?? (() => {}),
    };
  }

  /**
   * Execute a prompt with tool calling support
   */
  async executeWithTools(
    prompt: string,
    availableToolNames?: string[],
    systemPrompt?: string
  ): Promise<PipelineResult> {
    const startTime = Date.now();
    const messages: PipelineMessage[] = [];
    const allToolCalls: ToolCallResult[] = [];
    let turnCount = 0;

    // Add system prompt if provided
    if (systemPrompt) {
      messages.push({
        role: "system",
        content: systemPrompt,
      });
    }

    // Get available tools
    const availableTools = availableToolNames
      ? availableToolNames
          .map(name => this.registry.getToolByName(name))
          .filter((tool): tool is ToolSpec => tool !== undefined)
      : this.registry.getToolSpecs();

    // Convert tools to provider format
    const providerTools = this.convertToolsToProviderFormat(availableTools);

    // Initial user message
    messages.push({
      role: "user",
      content: prompt,
    });

    // Multi-turn tool calling loop
    while (turnCount < this.options.maxTurns) {
      turnCount++;

      if (this.options.verbose) {
        console.log(`[Pipeline] Turn ${turnCount}/${this.options.maxTurns}`);
      }

      // Call LLM with tools
      const response = await this.provider.complete(
        messages,
        providerTools.length > 0 ? providerTools : undefined,
        {
          temperature: 0.7,
          maxTokens: 4096,
        }
      );

      // Add assistant response to messages
      messages.push({
        role: "assistant",
        content: response.content,
        toolCalls: response.toolCalls,
      });

      // If no tool calls, we're done
      if (!response.toolCalls || response.toolCalls.length === 0) {
        const executionTime = Date.now() - startTime;
        return {
          content: response.content,
          toolCalls: allToolCalls,
          executionTimeMs: executionTime,
          turns: turnCount,
          modelResponse: response,
          metadata: {
            tokensUsed: response.usage
              ? response.usage.inputTokens + response.usage.outputTokens
              : undefined,
            modelUsed: response.model,
          },
        };
      }

      // Execute tool calls
      const toolResults: ToolCallResult[] = [];
      for (const toolCall of response.toolCalls) {
        await this.options.onToolCall(toolCall);

        const toolSpec = this.registry.getToolByName(toolCall.name);
        if (!toolSpec) {
          toolResults.push({
            callId: toolCall.id || `call-${Date.now()}`,
            toolName: toolCall.name,
            result: null,
            error: `Tool ${toolCall.name} not found`,
          });
          continue;
        }

        try {
          const execStartTime = Date.now();
          const execResult = await this.executor.execute(
            toolSpec,
            toolCall.arguments
          );
          const execTime = Date.now() - execStartTime;

          const result: ToolCallResult = {
            callId: toolCall.id || `call-${Date.now()}`,
            toolName: toolCall.name,
            result: execResult.result,
            error: execResult.error,
            metadata: {
              executionTimeMs: execTime,
            },
          };

          toolResults.push(result);
          allToolCalls.push(result);
          await this.options.onToolResult(result);
        } catch (error) {
          const result: ToolCallResult = {
            callId: toolCall.id || `call-${Date.now()}`,
            toolName: toolCall.name,
            result: null,
            error: error instanceof Error ? error.message : String(error),
          };
          toolResults.push(result);
          allToolCalls.push(result);
        }
      }

      // Add tool results to messages for next turn
      messages.push({
        role: "tool",
        content: JSON.stringify(toolResults),
        toolCallResults: toolResults,
      });
    }

    // Max turns reached
    const executionTime = Date.now() - startTime;
    const lastMessage = messages[messages.length - 1];
    return {
      content: lastMessage.content || "Max turns reached",
      toolCalls: allToolCalls,
      executionTimeMs: executionTime,
      turns: turnCount,
      modelResponse: messages[messages.length - 2],
      metadata: {},
    };
  }

  /**
   * Convert ToolSpec to provider-specific format
   */
  private convertToolsToProviderFormat(tools: ToolSpec[]): any[] {
    // Generic format that works with most providers
    return tools.map(tool => ({
      type: "function",
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.jsonSchema,
      },
    }));
  }
}

