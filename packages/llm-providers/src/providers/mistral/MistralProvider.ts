/**
 * Mistral AI Provider Implementation
 * 
 * Implements the LLMProvider interface for Mistral AI models.
 */
import { Mistral } from '@mistralai/mistralai';
import {
  LLMProvider,
  CompletionOptions,
  CompletionResult,
  CompletionChunk,
  Message,
  ToolSpec,
  ToolCall,
  Usage,
  ProviderCapabilities,
  RateLimitError,
  AuthenticationError,
  InvalidRequestError,
  ModelNotFoundError,
  LLMProviderError,
} from '../../domain/LLMProvider';

// Extend CompletionOptions to include model parameter
interface ExtendedCompletionOptions extends CompletionOptions {
  model?: string;
}

/**
 * Mistral AI Provider
 * 
 * Supports Mistral Large, Medium, Small, and Tiny models
 * with tool calling (function calling) support.
 */
export class MistralProvider implements LLMProvider {
  readonly name = 'mistral:mistral-large-latest';
  readonly maxContext = 32_000; // Mistral Large supports up to 32K tokens
  readonly pricePerMTokIn = 8.0; // Example pricing for Mistral Large
  readonly pricePerMTokOut = 24.0;
  readonly capabilities: ProviderCapabilities = {
    tools: true,
    vision: false, // Mistral doesn't support vision yet
    streaming: true,
    jsonMode: true,
  };

  private client: Mistral;
  private defaultModel: string;

  constructor(apiKey: string, defaultModel: string = 'mistral-large-latest') {
    if (!apiKey) {
      throw new AuthenticationError('Mistral API key is required');
    }

    this.client = new Mistral({ apiKey });
    this.defaultModel = defaultModel;
    this.name = `mistral:${defaultModel}`;
  }

  /**
   * Convert messages to Mistral format
   */
  private convertMessages(messages: Message[]): any[] {
    return messages.map((msg) => {
      const role = this.convertRole(msg.role);
      
      // Mistral uses a simple message format
      const content: any[] = [];

      if (msg.content) {
        content.push({ type: 'text', text: msg.content });
      }

      // Handle tool calls (function calls)
      if (msg.toolCalls && msg.toolCalls.length > 0) {
        for (const toolCall of msg.toolCalls) {
          content.push({
            type: 'tool_use',
            id: toolCall.id,
            name: toolCall.function.name,
            input: JSON.parse(toolCall.function.arguments),
          });
        }
      }

      // Handle tool responses
      if (msg.role === 'tool' && msg.toolCallId) {
        content.push({
          type: 'tool_result',
          tool_use_id: msg.toolCallId,
          content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content),
        });
      }

      return {
        role,
        content: content.length === 1 && content[0].type === 'text' ? content[0].text : content,
      };
    });
  }

  /**
   * Convert role to Mistral format
   */
  private convertRole(role: Message['role']): string {
    switch (role) {
      case 'user':
        return 'user';
      case 'assistant':
        return 'assistant';
      case 'system':
        return 'system';
      case 'tool':
        return 'user'; // Tool responses are treated as user messages
      default:
        return 'user';
    }
  }

  /**
   * Convert ToolSpec to Mistral tool format
   */
  private convertTools(tools: ToolSpec[]): any[] {
    return tools.map((tool) => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.jsonSchema,
      },
    }));
  }

  /**
   * Convert Mistral response to CompletionResult
   */
  private convertResponse(
    response: any,
    model: string,
    promptTokens: number = 0,
    completionTokens: number = 0
  ): CompletionResult {
    const content = response.choices[0]?.message?.content || '';
    const toolCalls: ToolCall[] = [];

    // Extract tool calls from response
    if (response.choices[0]?.message?.tool_calls) {
      for (const toolCall of response.choices[0].message.tool_calls) {
        toolCalls.push({
          id: toolCall.id || `call_${Date.now()}_${Math.random().toString(36).substring(7)}`,
          function: {
            name: toolCall.function.name,
            arguments: JSON.stringify(toolCall.function.arguments || {}),
          },
        });
      }
    }

    // Determine finish reason
    let finishReason: CompletionResult['finishReason'] = 'stop';
    if (toolCalls.length > 0) {
      finishReason = 'tool_calls';
    } else if (response.choices[0]?.finish_reason === 'length') {
      finishReason = 'length';
    } else if (response.choices[0]?.finish_reason === 'content_filter') {
      finishReason = 'content_filter';
    }

    // Calculate usage
    const usage: Usage = {
      promptTokens: promptTokens || response.usage?.prompt_tokens || this.estimateTokens(content),
      completionTokens: completionTokens || response.usage?.completion_tokens || this.estimateTokens(content),
      totalTokens: response.usage?.total_tokens || (promptTokens + completionTokens),
    };

    return {
      id: response.id || `gen_${Date.now()}`,
      content,
      model: this.name,
      usage,
      finishReason,
      toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
    };
  }

  /**
   * Estimate token count (rough approximation)
   */
  private estimateTokens(text: string): number {
    // Rough estimate: ~4 characters per token
    return Math.ceil(text.length / 4);
  }

  /**
   * Handle errors and convert to provider errors
   */
  private handleError(error: any): never {
    if (error.status === 429 || error.message?.includes('rate limit')) {
      throw new RateLimitError(
        'Mistral API rate limit exceeded',
        error.retryAfter || 60
      );
    }

    if (error.status === 401 || error.status === 403) {
      throw new AuthenticationError('Invalid Mistral API key');
    }

    if (error.status === 400) {
      throw new InvalidRequestError(error.message || 'Invalid request');
    }

    if (error.status === 404) {
      throw new ModelNotFoundError(`Model not found: ${this.defaultModel}`);
    }

    throw new LLMProviderError(
      `Mistral API error: ${error.message || 'Unknown error'}`,
      error
    );
  }

  /**
   * Complete a chat completion request
   */
  async completion(opts: ExtendedCompletionOptions): Promise<CompletionResult> {
    try {
      const modelName = opts.model || this.defaultModel;

      // Convert messages
      const mistralMessages = this.convertMessages(opts.messages);

      // Prepare options
      const options: any = {
        model: modelName,
        messages: mistralMessages,
        temperature: opts.temperature ?? 0.7,
        maxTokens: opts.maxTokens,
      };

      // Add tools if provided
      if (opts.tools && opts.tools.length > 0) {
        options.tools = this.convertTools(opts.tools);
      }

      // Add system message if provided
      if (opts.system) {
        options.systemPrompt = opts.system;
      }

      // Add response format if JSON mode
      if (opts.responseFormat === 'json_object') {
        options.responseFormat = { type: 'json_object' };
      }

      // Call Mistral API
      const response = await this.client.chat.complete(options);

      // Estimate tokens if not provided
      const promptText = opts.messages.map((m) => m.content).join('\n');
      const promptTokens = response.usage?.prompt_tokens || this.estimateTokens(promptText);
      const completionTokens = response.usage?.completion_tokens || this.estimateTokens(response.choices[0]?.message?.content || '');

      return this.convertResponse(response, modelName, promptTokens, completionTokens);
    } catch (error: any) {
      this.handleError(error);
    }
  }

  /**
   * Stream a chat completion request
   */
  async *streamCompletion(opts: ExtendedCompletionOptions): AsyncIterable<CompletionChunk> {
    try {
      const modelName = opts.model || this.defaultModel;

      // Convert messages
      const mistralMessages = this.convertMessages(opts.messages);

      // Prepare options
      const options: any = {
        model: modelName,
        messages: mistralMessages,
        temperature: opts.temperature ?? 0.7,
        maxTokens: opts.maxTokens,
        stream: true,
      };

      // Add tools if provided
      if (opts.tools && opts.tools.length > 0) {
        options.tools = this.convertTools(opts.tools);
      }

      // Add system message if provided
      if (opts.system) {
        options.systemPrompt = opts.system;
      }

      // Stream response
      const stream = await this.client.chat.stream(options);

      let accumulatedContent = '';
      let toolCalls: ToolCall[] = [];

      for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta;

        if (delta?.content) {
          accumulatedContent += delta.content;
          yield {
            content: delta.content,
          };
        }

        // Check for tool calls in chunk
        if (delta?.tool_calls) {
          for (const toolCall of delta.tool_calls) {
            if (toolCall.function) {
              const existingCall = toolCalls.find((tc) => tc.id === toolCall.id);
              if (existingCall) {
                // Append to existing call
                const currentArgs = JSON.parse(existingCall.function.arguments);
                const newArgs = { ...currentArgs, ...toolCall.function.arguments };
                existingCall.function.arguments = JSON.stringify(newArgs);
              } else {
                // New tool call
                toolCalls.push({
                  id: toolCall.id || `call_${Date.now()}_${Math.random().toString(36).substring(7)}`,
                  function: {
                    name: toolCall.function.name,
                    arguments: JSON.stringify(toolCall.function.arguments || {}),
                  },
                });
              }
            }
          }
        }

        // Check if finished
        if (chunk.choices[0]?.finish_reason) {
          if (toolCalls.length > 0) {
            yield {
              content: '',
              toolCalls,
              finishReason: 'tool_calls',
            };
          } else {
            yield {
              content: '',
              finishReason: chunk.choices[0].finish_reason === 'length' ? 'length' : 'stop',
            };
          }
          break;
        }
      }
    } catch (error: any) {
      this.handleError(error);
    }
  }
}

