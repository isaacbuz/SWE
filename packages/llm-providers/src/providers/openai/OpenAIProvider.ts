import OpenAI from 'openai';
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
 * OpenAI Provider Implementation
 * 
 * Implements the LLMProvider interface for OpenAI's API, supporting
 * GPT-4, GPT-4 Turbo, and other OpenAI models.
 */
export class OpenAIProvider implements LLMProvider {
  readonly name: string;
  readonly maxContext: number;
  readonly pricePerMTokIn: number;
  readonly pricePerMTokOut: number;
  readonly capabilities = {
    tools: true,
    vision: true,
    streaming: true,
    jsonMode: true,
  };

  private client: OpenAI;
  private model: string;

  constructor(
    apiKey: string,
    model: string = 'gpt-4-turbo-preview',
    options?: {
      baseURL?: string;
      maxContext?: number;
      pricePerMTokIn?: number;
      pricePerMTokOut?: number;
    }
  ) {
    this.client = new OpenAI({ apiKey, baseURL: options?.baseURL });
    this.model = model;
    this.name = `openai:${model}`;
    this.maxContext = options?.maxContext ?? 128_000;
    this.pricePerMTokIn = options?.pricePerMTokIn ?? 10.0;
    this.pricePerMTokOut = options?.pricePerMTokOut ?? 30.0;
  }

  async completion(opts: CompletionOptions): Promise<CompletionResult> {
    try {
      // Convert ToolSpec[] to OpenAI function format
      const functions = opts.tools?.map(this.convertToolSpecToOpenAI) || undefined;

      // Prepare messages
      const messages = this.convertMessages(opts.messages);

      // Prepare system message
      const systemMessage = opts.system;

      // Call OpenAI API
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: systemMessage
          ? [{ role: 'system', content: systemMessage }, ...messages]
          : messages,
        functions,
        function_call: functions ? 'auto' : undefined,
        temperature: opts.temperature ?? 0.7,
        max_tokens: opts.maxTokens,
        response_format: opts.responseFormat === 'json_object' ? { type: 'json_object' } : undefined,
        stop: opts.stopSequences,
      });

      const choice = response.choices[0];
      if (!choice) {
        throw new InvalidRequestError('No completion returned from OpenAI');
      }

      // Parse tool calls
      const toolCalls = choice.message.function_calls?.map(this.convertOpenAIToolCall) || undefined;

      // Build usage
      const usage: Usage = {
        promptTokens: response.usage?.prompt_tokens ?? 0,
        completionTokens: response.usage?.completion_tokens ?? 0,
        totalTokens: response.usage?.total_tokens ?? 0,
      };

      // Map finish reason
      const finishReason = this.mapFinishReason(choice.finish_reason);

      return {
        content: choice.message.content || '',
        toolCalls,
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
      // Convert ToolSpec[] to OpenAI function format
      const functions = opts.tools?.map(this.convertToolSpecToOpenAI) || undefined;

      // Prepare messages
      const messages = this.convertMessages(opts.messages);

      // Prepare system message
      const systemMessage = opts.system;

      // Call OpenAI API with streaming
      const stream = await this.client.chat.completions.create({
        model: this.model,
        messages: systemMessage
          ? [{ role: 'system', content: systemMessage }, ...messages]
          : messages,
        functions,
        function_call: functions ? 'auto' : undefined,
        temperature: opts.temperature ?? 0.7,
        max_tokens: opts.maxTokens,
        response_format: opts.responseFormat === 'json_object' ? { type: 'json_object' } : undefined,
        stop: opts.stopSequences,
        stream: true,
      });

      for await (const chunk of stream) {
        const choice = chunk.choices[0];
        if (!choice) continue;

        const delta = choice.delta;

        // Parse tool calls if present
        const toolCalls = delta.function_calls?.map((fc: any) => ({
          id: fc.id || '',
          type: 'function' as const,
          function: {
            name: fc.name || '',
            arguments: fc.arguments || '',
          },
        }));

        yield {
          content: delta.content || '',
          finishReason: choice.finish_reason
            ? this.mapFinishReason(choice.finish_reason)
            : undefined,
          toolCalls,
        };
      }
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Convert ToolSpec to OpenAI function format
   */
  private convertToolSpecToOpenAI(tool: ToolSpec): OpenAI.Chat.Completions.ChatCompletionCreateParams.Function {
    return {
      name: tool.name,
      description: tool.description,
      parameters: tool.jsonSchema as OpenAI.Chat.Completions.ChatCompletionCreateParams.Function.Parameters,
    };
  }

  /**
   * Convert messages to OpenAI format
   */
  private convertMessages(messages: Array<{ role: string; content: string; toolCalls?: ToolCall[]; toolCallId?: string }>): OpenAI.Chat.Completions.ChatCompletionMessageParam[] {
    return messages.map((msg) => {
      if (msg.role === 'tool' && msg.toolCallId) {
        return {
          role: 'tool',
          content: msg.content,
          tool_call_id: msg.toolCallId,
        };
      }

      if (msg.role === 'assistant' && msg.toolCalls) {
        return {
          role: 'assistant',
          content: msg.content || null,
          tool_calls: msg.toolCalls.map((tc) => ({
            id: tc.id,
            type: 'function',
            function: {
              name: tc.function.name,
              arguments: tc.function.arguments,
            },
          })),
        };
      }

      return {
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
      };
    });
  }

  /**
   * Convert OpenAI tool call to standard format
   */
  private convertOpenAIToolCall(fc: OpenAI.Chat.Completions.ChatCompletionMessage.FunctionCall): ToolCall {
    return {
      id: fc.name, // OpenAI doesn't provide ID in non-streaming, use name as fallback
      type: 'function',
      function: {
        name: fc.name,
        arguments: fc.arguments,
      },
    };
  }

  /**
   * Map OpenAI finish reason to standard format
   */
  private mapFinishReason(reason: string | null): 'stop' | 'length' | 'tool_calls' | 'content_filter' {
    switch (reason) {
      case 'stop':
        return 'stop';
      case 'length':
        return 'length';
      case 'function_call':
        return 'tool_calls';
      case 'content_filter':
        return 'content_filter';
      default:
        return 'stop';
    }
  }

  /**
   * Handle OpenAI API errors
   */
  private handleError(error: unknown): Error {
    if (error instanceof OpenAI.APIError) {
      if (error.status === 401) {
        return new AuthenticationError('Invalid OpenAI API key');
      }
      if (error.status === 429) {
        const retryAfter = error.headers?.['retry-after']
          ? parseInt(error.headers['retry-after'] as string, 10)
          : undefined;
        return new RateLimitError('OpenAI rate limit exceeded', retryAfter);
      }
      if (error.status === 400) {
        return new InvalidRequestError(error.message || 'Invalid request to OpenAI');
      }
      if (error.status === 404) {
        return new ModelNotFoundError('OpenAI model not found');
      }
      return new InvalidRequestError(error.message || 'OpenAI API error');
    }

    if (error instanceof Error) {
      return new InvalidRequestError(error.message);
    }

    return new InvalidRequestError('Unknown error occurred');
  }
}

