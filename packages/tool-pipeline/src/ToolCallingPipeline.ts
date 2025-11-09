import {
  LLMProvider,
  Message,
  ToolCall,
  CompletionResult,
  CompletionOptions,
} from '@ai-company/llm-providers';
import { ToolRegistry, ToolSpec } from '@ai-company/openapi-tools';
import { ToolExecutor, ToolResult } from '@ai-company/tool-executor';

/**
 * Pipeline result
 */
export interface PipelineResult {
  content: string;
  turns: number;
  toolCalls?: ToolCall[];
  cost?: number;
  executionResults?: ToolResult[];
}

/**
 * Pipeline options
 */
export interface PipelineOptions {
  /**
   * Maximum number of tool calling turns
   * @default 5
   */
  maxTurns?: number;

  /**
   * Whether to execute tools in parallel when safe
   * @default true
   */
  parallelExecution?: boolean;

  /**
   * Timeout per turn in milliseconds
   * @default 30000
   */
  timeoutMs?: number;

  /**
   * Whether to include tool execution results in final response
   * @default true
   */
  includeToolResults?: boolean;
}

/**
 * ToolCallingPipeline - End-to-end tool calling pipeline
 * 
 * Orchestrates multi-turn conversations between LLM and tools:
 * 1. LLM generates response with potential tool calls
 * 2. Tools are executed
 * 3. Results are fed back to LLM
 * 4. Process repeats until LLM provides final answer
 */
export class ToolCallingPipeline {
  constructor(
    private toolRegistry: ToolRegistry,
    private toolExecutor: ToolExecutor,
    private provider: LLMProvider
  ) {}

  /**
   * Execute pipeline with tools
   * 
   * @param prompt - Initial user prompt
   * @param availableTools - List of tool names to make available
   * @param options - Pipeline options
   * @returns Final result with content and execution details
   */
  async executeWithTools(
    prompt: string,
    availableTools: string[],
    options: PipelineOptions = {}
  ): Promise<PipelineResult> {
    const opts: Required<PipelineOptions> = {
      maxTurns: options.maxTurns ?? 5,
      parallelExecution: options.parallelExecution ?? true,
      timeoutMs: options.timeoutMs ?? 30000,
      includeToolResults: options.includeToolResults ?? true,
    };

    // Get tool specs from registry
    const toolSpecs = this.getToolSpecs(availableTools);

    // Initialize conversation
    const messages: Message[] = [
      { role: 'user', content: prompt },
    ];

    let turns = 0;
    const executionResults: ToolResult[] = [];
    let totalCost = 0;

    while (turns < opts.maxTurns) {
      // Convert tool specs to provider format
      const providerToolSpecs = this.convertToolSpecsToProvider(toolSpecs);

      // Call LLM with tools
      const completionOptions: CompletionOptions = {
        messages,
        tools: providerToolSpecs,
        temperature: 0.7,
        maxTokens: 4096,
      };

      const result: CompletionResult = await Promise.race([
        this.provider.completion(completionOptions),
        new Promise<CompletionResult>((_, reject) =>
          setTimeout(() => reject(new Error('Pipeline timeout')), opts.timeoutMs)
        ),
      ]);

      // Estimate cost
      const cost = this.estimateCost(result.usage);
      totalCost += cost;

      // If no tool calls, we're done
      if (!result.toolCalls || result.toolCalls.length === 0) {
        return {
          content: result.content,
          turns: turns + 1,
          cost: totalCost,
          executionResults: opts.includeToolResults ? executionResults : undefined,
        };
      }

      // Execute tools
      const toolResults = await this.executeTools(
        result.toolCalls,
        opts.parallelExecution
      );

      executionResults.push(...toolResults);

      // Add assistant message with tool calls
      messages.push({
        role: 'assistant',
        content: result.content,
        toolCalls: result.toolCalls,
      });

      // Add tool results as tool messages
      for (let i = 0; i < result.toolCalls.length; i++) {
        const toolCall = result.toolCalls[i];
        const toolResult = toolResults[i];

        messages.push({
          role: 'tool',
          content: toolResult.success
            ? JSON.stringify(toolResult.result)
            : JSON.stringify({ error: toolResult.error }),
          toolCallId: toolCall.id,
        });
      }

      turns++;
    }

    // Max turns exceeded
    throw new Error(
      `Max turns (${opts.maxTurns}) exceeded. Pipeline may be stuck in a loop.`
    );
  }

  /**
   * Get tool specs from registry
   */
  private getToolSpecs(toolNames: string[]): ToolSpec[] {
    const specs: ToolSpec[] = [];

    for (const name of toolNames) {
      const spec = this.toolRegistry.getToolByName(name);
      if (spec) {
        specs.push(spec);
      } else {
        console.warn(`Tool ${name} not found in registry`);
      }
    }

    return specs;
  }

  /**
   * Convert ToolSpec[] to provider-specific format
   */
  private convertToolSpecsToProvider(toolSpecs: ToolSpec[]): ToolSpec[] {
    // ToolSpec is already in a format compatible with providers
    // Providers will convert it to their specific format
    return toolSpecs;
  }

  /**
   * Execute tools (potentially in parallel)
   */
  private async executeTools(
    toolCalls: ToolCall[],
    parallel: boolean
  ): Promise<ToolResult[]> {
    const executions = toolCalls.map(async (toolCall) => {
      const toolName = toolCall.function.name;
      let args: unknown;

      try {
        args = JSON.parse(toolCall.function.arguments);
      } catch (error) {
        return {
          toolName,
          result: null,
          durationMs: 0,
          success: false,
          error: `Invalid JSON arguments: ${error instanceof Error ? error.message : String(error)}`,
        } as ToolResult;
      }

      // Check if tool is registered in executor
      if (!this.toolExecutor.hasTool(toolName)) {
        return {
          toolName,
          result: null,
          durationMs: 0,
          success: false,
          error: `Tool ${toolName} not registered in executor`,
        } as ToolResult;
      }

      return await this.toolExecutor.execute(toolName, args);
    });

    if (parallel) {
      // Execute all tools in parallel
      return Promise.all(executions);
    } else {
      // Execute sequentially
      const results: ToolResult[] = [];
      for (const execution of executions) {
        results.push(await execution);
      }
      return results;
    }
  }

  /**
   * Estimate cost from usage
   */
  private estimateCost(usage: { promptTokens: number; completionTokens: number }): number {
    const inputCost = (usage.promptTokens / 1_000_000) * this.provider.pricePerMTokIn;
    const outputCost = (usage.completionTokens / 1_000_000) * this.provider.pricePerMTokOut;
    return inputCost + outputCost;
  }
}

