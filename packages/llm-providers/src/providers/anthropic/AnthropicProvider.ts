import Anthropic from '@anthropic-ai/sdk';
import {
  LLMProvider,
  CompletionOptions,
  CompletionResult,
  CompletionChunk,
  ToolSpec,
  ToolCall,
  Usage,
  RateLimitError,
  AuthenticationError,
  InvalidRequestError,
  ModelNotFoundError,
} from '../../domain/LLMProvider';

/**
 * Anthropic Provider Implementation
 * 
 * Implements the LLMProvider interface for Anthropic's Claude API,
 * supporting Claude 3 Opus, Sonnet, and Haiku models.
 */
export class AnthropicProvider implements LLMProvider {
  readonly name: string;
  readonly maxContext: number;
  readonly pricePerMTokIn: number;
  readonly pricePerMTokOut: number;
  readonly capabilities = {
    tools: true,
    vision: true,
    streaming: true,
    jsonMode: false, // Claude doesn't have native JSON mode
  };

  private client: Anthropic;
  private model: string;

  constructor(
    apiKey: string,
    model: string = 'claude-3-sonnet-20240229',
    options?: {
      baseURL?: string;
      maxContext?: number;
      pricePerMTokIn?: number;
      pricePerMTokOut?: number;
    }
  ) {
    this.client = new Anthropic({ apiKey, baseURL: options?.baseURL });
    this.model = model;
    this.name = `anthropic:${model}`;
    this.maxContext = options?.maxContext ?? 200_000;
    this.pricePerMTokIn = options?.pricePerMTokIn ?? 3.0;
    this.pricePerMTokOut = options?.pricePerMTokOut ?? 15.0;
  }

  async completion(opts: CompletionOptions): Promise<CompletionResult> {
    try {
      // Convert ToolSpec[] to Anthropic tool format
      const tools = opts.tools?.map(this.convertToolSpecToAnthropic) || undefined;

      // Convert messages (Anthropic uses different format)
      const messages = this.convertMessages(opts.messages);

      // Call Anthropic API
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: opts.maxTokens ?? 4096,
        temperature: opts.temperature ?? 0.7,
        system: opts.system,
        messages,
        tools,
        stop_sequences: opts.stopSequences,
      });

      // Extract content
      const content = response.content
        .filter((block) => block.type === 'text')
        .map((block) => (block as Anthropic.TextBlock).text)
        .join('');

      // Parse tool use blocks
      const toolCalls = response.content
        .filter((block) => block.type === 'tool_use')
        .map((block) => this.convertAnthropicToolUse(block as Anthropic.ToolUseBlock));

      // Build usage
      const usage: Usage = {
        promptTokens: response.usage.input_tokens,
        completionTokens: response.usage.output_tokens,
        totalTokens: response.usage.input_tokens + response.usage.output_tokens,
        cacheCreationTokens: response.usage.cache_creation_input_tokens,
        cacheReadTokens: response.usage.cache_read_input_tokens,
      };

      // Map stop reason
      const finishReason = this.mapStopReason(response.stop_reason);

      return {
        content,
        toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
        usage,
        finishReason,
        model: response.model,
      };
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async *streamCompletion(opts: CompletionOptions): AsyncIterable<CompletionChunk> {
    try {
      // Convert ToolSpec[] to Anthropic tool format
      const tools = opts.tools?.map(this.convertToolSpecToAnthropic) || undefined;

      // Convert messages
      const messages = this.convertMessages(opts.messages);

      // Call Anthropic API with streaming
      const stream = await this.client.messages.stream({
        model: this.model,
        max_tokens: opts.maxTokens ?? 4096,
        temperature: opts.temperature ?? 0.7,
        system: opts.system,
        messages,
        tools,
        stop_sequences: opts.stopSequences,
      });

      for await (const event of stream) {
        if (event.type === 'content_block_delta') {
          yield {
            content: event.delta.text || '',
          };
        } else if (event.type === 'content_block_stop') {
          // Tool use blocks are handled separately
        } else if (event.type === 'message_delta') {
          // Handle delta updates
        } else if (event.type === 'message_stop') {
          const stopReason = (event as any).stop_reason;
          yield {
            content: '',
            finishReason: this.mapStopReason(stopReason),
          };
        }
      }
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Convert ToolSpec to Anthropic tool format
   */
  private convertToolSpecToAnthropic(tool: ToolSpec): Anthropic.Tool {
    return {
      name: tool.name,
      description: tool.description,
      input_schema: tool.jsonSchema as Anthropic.Tool.InputSchema,
    };
  }

  /**
   * Convert messages to Anthropic format
   */
  private convertMessages(
    messages: Array<{ role: string; content: string; toolCalls?: ToolCall[]; toolCallId?: string }>
  ): Anthropic.MessageParam[] {
    return messages
      .filter((msg) => msg.role !== 'system') // System is separate in Anthropic
      .map((msg) => {
        if (msg.role === 'user') {
          return {
            role: 'user',
            content: msg.content,
          };
        }

        if (msg.role === 'assistant') {
          const content: Anthropic.TextBlock[] = [];
          
          if (msg.content) {
            content.push({ type: 'text', text: msg.content });
          }

          if (msg.toolCalls) {
            // Convert tool calls to tool use blocks
            for (const tc of msg.toolCalls) {
              content.push({
                type: 'tool_use',
                id: tc.id,
                name: tc.function.name,
                input: JSON.parse(tc.function.arguments),
              });
            }
          }

          return {
            role: 'assistant',
            content,
          };
        }

        // Tool role - convert to user message with tool results
        if (msg.role === 'tool' && msg.toolCallId) {
          return {
            role: 'user',
            content: [
              {
                type: 'tool_result',
                tool_use_id: msg.toolCallId,
                content: msg.content,
              },
            ],
          };
        }

        // Default: treat as user message
        return {
          role: 'user',
          content: msg.content,
        };
      });
  }

  /**
   * Convert Anthropic tool use block to standard format
   */
  private convertAnthropicToolUse(block: Anthropic.ToolUseBlock): ToolCall {
    return {
      id: block.id,
      type: 'function',
      function: {
        name: block.name,
        arguments: JSON.stringify(block.input),
      },
    };
  }

  /**
   * Map Anthropic stop reason to standard format
   */
  private mapStopReason(reason: 'end_turn' | 'max_tokens' | 'stop_sequence' | 'tool_use'): 'stop' | 'length' | 'tool_calls' | 'content_filter' {
    switch (reason) {
      case 'end_turn':
        return 'stop';
      case 'max_tokens':
        return 'length';
      case 'tool_use':
        return 'tool_calls';
      case 'stop_sequence':
        return 'stop';
      default:
        return 'stop';
    }
  }

  /**
   * Handle Anthropic API errors
   */
  private handleError(error: unknown): Error {
    if (error instanceof Anthropic.APIError) {
      if (error.status === 401) {
        return new AuthenticationError('Invalid Anthropic API key');
      }
      if (error.status === 429) {
        const retryAfter = error.headers?.['retry-after']
          ? parseInt(error.headers['retry-after'] as string, 10)
          : undefined;
        return new RateLimitError('Anthropic rate limit exceeded', retryAfter);
      }
      if (error.status === 400) {
        return new InvalidRequestError(error.message || 'Invalid request to Anthropic');
      }
      if (error.status === 404) {
        return new ModelNotFoundError('Anthropic model not found');
      }
      return new InvalidRequestError(error.message || 'Anthropic API error');
    }

    if (error instanceof Error) {
      return new InvalidRequestError(error.message);
    }

    return new InvalidRequestError('Unknown error occurred');
  }
}

