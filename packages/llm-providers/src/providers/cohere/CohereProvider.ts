/**
 * Cohere Provider Implementation
 * 
 * Implements the LLMProvider interface for Cohere AI models.
 */
import { CohereClient } from 'cohere-ai';
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
 * Cohere Provider
 * 
 * Supports Cohere Command, Command Light, and other models
 * with tool calling (function calling) support.
 */
export class CohereProvider implements LLMProvider {
  readonly name = 'cohere:command';
  readonly maxContext = 4_096; // Cohere Command supports up to 4K tokens
  readonly pricePerMTokIn = 1.0; // Example pricing for Command
  readonly pricePerMTokOut = 2.0;
  readonly capabilities: ProviderCapabilities = {
    tools: true,
    vision: false, // Cohere doesn't support vision yet
    streaming: true,
    jsonMode: false, // Cohere doesn't have explicit JSON mode
  };

  private client: CohereClient;
  private defaultModel: string;

  constructor(apiKey: string, defaultModel: string = 'command') {
    if (!apiKey) {
      throw new AuthenticationError('Cohere API key is required');
    }

    this.client = new CohereClient({ token: apiKey });
    this.defaultModel = defaultModel;
    this.name = `cohere:${defaultModel}`;
  }

  /**
   * Convert messages to Cohere format
   */
  private convertMessages(messages: Message[]): { message: string; documents?: any[] }[] {
    const cohereMessages: { message: string; documents?: any[] }[] = [];

    for (const msg of messages) {
      if (msg.role === 'system') {
        // Cohere doesn't have system messages, prepend to first user message
        continue;
      }

      if (msg.role === 'user' || msg.role === 'tool') {
        let content = msg.content || '';

        // Handle tool responses
        if (msg.role === 'tool' && msg.toolCallId) {
          content = `Tool result: ${content}`;
        }

        cohereMessages.push({ message: content });
      } else if (msg.role === 'assistant') {
        let content = msg.content || '';

        // Handle tool calls
        if (msg.toolCalls && msg.toolCalls.length > 0) {
          const toolCallTexts = msg.toolCalls.map((tc) => 
            `Calling tool ${tc.function.name} with args: ${tc.function.arguments}`
          );
          content = `${content}\n${toolCallTexts.join('\n')}`;
        }

        cohereMessages.push({ message: content });
      }
    }

    return cohereMessages;
  }

  /**
   * Convert ToolSpec to Cohere tool format
   */
  private convertTools(tools: ToolSpec[]): any[] {
    return tools.map((tool) => ({
      name: tool.name,
      description: tool.description,
      parameterDefinitions: this.convertJsonSchemaToCohere(tool.jsonSchema),
    }));
  }

  /**
   * Convert JSON Schema to Cohere parameter definitions format
   */
  private convertJsonSchemaToCohere(jsonSchema: any): any {
    const parameters: any = {};

    if (jsonSchema.properties) {
      for (const [key, value] of Object.entries(jsonSchema.properties as Record<string, any>)) {
        parameters[key] = {
          description: value.description || '',
          type: this.mapJsonSchemaType(value.type),
          required: jsonSchema.required?.includes(key) || false,
        };
      }
    }

    return parameters;
  }

  /**
   * Map JSON Schema type to Cohere type
   */
  private mapJsonSchemaType(type: string): string {
    switch (type) {
      case 'string':
        return 'string';
      case 'number':
      case 'integer':
        return 'number';
      case 'boolean':
        return 'boolean';
      case 'array':
        return 'array';
      case 'object':
        return 'object';
      default:
        return 'string';
    }
  }

  /**
   * Convert Cohere response to CompletionResult
   */
  private convertResponse(
    response: any,
    model: string,
    promptTokens: number = 0,
    completionTokens: number = 0
  ): CompletionResult {
    const content = response.text || '';
    const toolCalls: ToolCall[] = [];

    // Extract tool calls from response (Cohere returns tool calls in metadata)
    if (response.toolCalls && response.toolCalls.length > 0) {
      for (const toolCall of response.toolCalls) {
        toolCalls.push({
          id: toolCall.id || `call_${Date.now()}_${Math.random().toString(36).substring(7)}`,
          function: {
            name: toolCall.name,
            arguments: JSON.stringify(toolCall.parameters || {}),
          },
        });
      }
    }

    // Determine finish reason
    let finishReason: CompletionResult['finishReason'] = 'stop';
    if (toolCalls.length > 0) {
      finishReason = 'tool_calls';
    } else if (response.finishReason === 'MAX_TOKENS') {
      finishReason = 'length';
    } else if (response.finishReason === 'COMPLETE') {
      finishReason = 'stop';
    }

    // Calculate usage
    const usage: Usage = {
      promptTokens: promptTokens || response.meta?.tokens?.inputTokens || this.estimateTokens(content),
      completionTokens: completionTokens || response.meta?.tokens?.outputTokens || this.estimateTokens(content),
      totalTokens: response.meta?.tokens?.totalTokens || (promptTokens + completionTokens),
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
        'Cohere API rate limit exceeded',
        error.retryAfter || 60
      );
    }

    if (error.status === 401 || error.status === 403) {
      throw new AuthenticationError('Invalid Cohere API key');
    }

    if (error.status === 400) {
      throw new InvalidRequestError(error.message || 'Invalid request');
    }

    if (error.status === 404) {
      throw new ModelNotFoundError(`Model not found: ${this.defaultModel}`);
    }

    throw new LLMProviderError(
      `Cohere API error: ${error.message || 'Unknown error'}`,
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
      const cohereMessages = this.convertMessages(opts.messages);
      
      // Extract chat history and current message
      const chatHistory = cohereMessages.slice(0, -1).map((m) => m.message);
      const message = cohereMessages[cohereMessages.length - 1]?.message || '';

      // Prepare options
      const options: any = {
        model: modelName,
        message,
        chatHistory: chatHistory.length > 0 ? chatHistory : undefined,
        temperature: opts.temperature ?? 0.7,
        maxTokens: opts.maxTokens,
      };

      // Add system prompt if provided
      if (opts.system) {
        options.preamble = opts.system;
      }

      // Add tools if provided
      if (opts.tools && opts.tools.length > 0) {
        options.tools = this.convertTools(opts.tools);
        options.toolResults = []; // Will be populated in multi-turn conversations
      }

      // Call Cohere API
      const response = await this.client.chat(options);

      // Estimate tokens if not provided
      const promptText = opts.messages.map((m) => m.content).join('\n');
      const promptTokens = response.meta?.tokens?.inputTokens || this.estimateTokens(promptText);
      const completionTokens = response.meta?.tokens?.outputTokens || this.estimateTokens(response.text || '');

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
      const cohereMessages = this.convertMessages(opts.messages);
      
      // Extract chat history and current message
      const chatHistory = cohereMessages.slice(0, -1).map((m) => m.message);
      const message = cohereMessages[cohereMessages.length - 1]?.message || '';

      // Prepare options
      const options: any = {
        model: modelName,
        message,
        chatHistory: chatHistory.length > 0 ? chatHistory : undefined,
        temperature: opts.temperature ?? 0.7,
        maxTokens: opts.maxTokens,
        stream: true,
      };

      // Add system prompt if provided
      if (opts.system) {
        options.preamble = opts.system;
      }

      // Add tools if provided
      if (opts.tools && opts.tools.length > 0) {
        options.tools = this.convertTools(opts.tools);
      }

      // Stream response
      const stream = await this.client.chatStream(options);

      let accumulatedContent = '';
      let toolCalls: ToolCall[] = [];

      for await (const event of stream) {
        if (event.type === 'text-generation') {
          const text = event.text || '';
          accumulatedContent += text;
          yield {
            content: text,
          };
        }

        // Check for tool calls in event
        if (event.type === 'tool-calls' && event.toolCalls) {
          for (const toolCall of event.toolCalls) {
            toolCalls.push({
              id: toolCall.id || `call_${Date.now()}_${Math.random().toString(36).substring(7)}`,
              function: {
                name: toolCall.name,
                arguments: JSON.stringify(toolCall.parameters || {}),
              },
            });
          }
        }

        // Check if finished
        if (event.type === 'stream-end') {
          if (toolCalls.length > 0) {
            yield {
              content: '',
              toolCalls,
              finishReason: 'tool_calls',
            };
          } else {
            yield {
              content: '',
              finishReason: 'stop',
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

