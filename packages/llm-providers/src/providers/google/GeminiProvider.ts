/**
 * Google Gemini Provider Implementation
 * 
 * Implements the LLMProvider interface for Google's Gemini models.
 */
import { GoogleGenerativeAI } from '@google/generative-ai';
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

/**
 * Google Gemini Provider
 * 
 * Supports Gemini Pro, Gemini Pro Vision, and Gemini Ultra models
 * with tool calling (function calling) support.
 */
export class GeminiProvider implements LLMProvider {
  readonly name = 'google:gemini-pro';
  readonly maxContext = 1_000_000; // Gemini 1.5 Pro supports up to 1M tokens
  readonly pricePerMTokIn = 1.25; // Example pricing for Gemini Pro
  readonly pricePerMTokOut = 5.0;
  readonly capabilities: ProviderCapabilities = {
    tools: true,
    vision: true,
    streaming: true,
    jsonMode: true,
  };

  private client: GoogleGenerativeAI;
  private defaultModel: string;

  constructor(apiKey: string, defaultModel: string = 'gemini-pro') {
    if (!apiKey) {
      throw new AuthenticationError('Google API key is required');
    }

    this.client = new GoogleGenerativeAI(apiKey);
    this.defaultModel = defaultModel;
    this.name = `google:${defaultModel}`;
  }

  /**
   * Convert messages to Gemini format
   */
  private convertMessages(messages: Message[]): any[] {
    return messages.map((msg) => {
      const role = this.convertRole(msg.role);
      const parts: any[] = [];

      if (msg.content) {
        parts.push({ text: msg.content });
      }

      // Handle tool calls (function calls)
      if (msg.toolCalls && msg.toolCalls.length > 0) {
        for (const toolCall of msg.toolCalls) {
          parts.push({
            functionCall: {
              name: toolCall.function.name,
              args: JSON.parse(toolCall.function.arguments),
            },
          });
        }
      }

      // Handle tool responses
      if (msg.role === 'tool' && msg.toolCallId) {
        parts.push({
          functionResponse: {
            name: msg.toolCalls?.[0]?.function.name || 'unknown',
            response: typeof msg.content === 'string' ? JSON.parse(msg.content) : msg.content,
          },
        });
      }

      return {
        role,
        parts,
      };
    });
  }

  /**
   * Convert role to Gemini format
   */
  private convertRole(role: Message['role']): string {
    switch (role) {
      case 'user':
        return 'user';
      case 'assistant':
        return 'model';
      case 'system':
        return 'user'; // Gemini doesn't have system role, prepend to first user message
      case 'tool':
        return 'user'; // Tool responses are treated as user messages
      default:
        return 'user';
    }
  }

  /**
   * Convert ToolSpec to Gemini function declaration format
   */
  private convertTools(tools: ToolSpec[]): any[] {
    return tools.map((tool) => ({
      functionDeclarations: [
        {
          name: tool.name,
          description: tool.description,
          parameters: tool.parameters,
        },
      ],
    }));
  }

  /**
   * Convert Gemini response to CompletionResult
   */
  private convertResponse(
    response: any,
    model: string,
    promptTokens: number = 0,
    completionTokens: number = 0
  ): CompletionResult {
    const content = response.text() || '';
    const toolCalls: ToolCall[] = [];

    // Extract function calls from response
    if (response.functionCalls && response.functionCalls.length > 0) {
      for (const funcCall of response.functionCalls) {
        toolCalls.push({
          id: `call_${Date.now()}_${Math.random().toString(36).substring(7)}`,
          function: {
            name: funcCall.name,
            arguments: JSON.stringify(funcCall.args || {}),
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
    } else if (response.finishReason === 'SAFETY') {
      finishReason = 'content_filter';
    }

    // Calculate usage if not provided
    const usage: Usage = {
      promptTokens: promptTokens || this.estimateTokens(content),
      completionTokens: completionTokens || this.estimateTokens(content),
      totalTokens: (promptTokens || 0) + (completionTokens || 0),
    };

    return {
      id: response.responseId || `gen_${Date.now()}`,
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
    if (error.status === 429 || error.message?.includes('quota')) {
      throw new RateLimitError(
        'Google API rate limit exceeded',
        error.retryAfter || 60
      );
    }

    if (error.status === 401 || error.status === 403) {
      throw new AuthenticationError('Invalid Google API key');
    }

    if (error.status === 400) {
      throw new InvalidRequestError(error.message || 'Invalid request');
    }

    if (error.status === 404) {
      throw new ModelNotFoundError(`Model not found: ${this.defaultModel}`);
    }

    throw new LLMProviderError(
      `Google API error: ${error.message || 'Unknown error'}`,
      error
    );
  }

  /**
   * Complete a chat completion request
   */
  async completion(opts: CompletionOptions): Promise<CompletionResult> {
    try {
      const model = this.client.getGenerativeModel({
        model: opts.model || this.defaultModel,
      });

      // Convert messages
      const geminiMessages = this.convertMessages(opts.messages);

      // Prepare generation config
      const generationConfig: any = {
        temperature: opts.temperature ?? 0.7,
        maxOutputTokens: opts.maxTokens,
      };

      // Add tools if provided
      let tools: any[] | undefined;
      if (opts.tools && opts.tools.length > 0) {
        tools = this.convertTools(opts.tools);
      }

      // Start chat
      const chat = model.startChat({
        history: geminiMessages.slice(0, -1), // All but last message
        generationConfig,
        tools,
      });

      // Send last message
      const lastMessage = geminiMessages[geminiMessages.length - 1];
      const result = await chat.sendMessage(lastMessage.parts);

      const response = result.response;

      // Estimate tokens (Gemini API doesn't always provide token counts)
      const promptText = opts.messages.map((m) => m.content).join('\n');
      const promptTokens = this.estimateTokens(promptText);
      const completionTokens = this.estimateTokens(response.text());

      return this.convertResponse(response, opts.model || this.defaultModel, promptTokens, completionTokens);
    } catch (error: any) {
      this.handleError(error);
    }
  }

  /**
   * Stream a chat completion request
   */
  async *streamCompletion(opts: CompletionOptions): AsyncIterable<CompletionChunk> {
    try {
      const model = this.client.getGenerativeModel({
        model: opts.model || this.defaultModel,
      });

      // Convert messages
      const geminiMessages = this.convertMessages(opts.messages);

      // Prepare generation config
      const generationConfig: any = {
        temperature: opts.temperature ?? 0.7,
        maxOutputTokens: opts.maxTokens,
      };

      // Add tools if provided
      let tools: any[] | undefined;
      if (opts.tools && opts.tools.length > 0) {
        tools = this.convertTools(opts.tools);
      }

      // Start chat
      const chat = model.startChat({
        history: geminiMessages.slice(0, -1),
        generationConfig,
        tools,
      });

      // Send last message and stream
      const lastMessage = geminiMessages[geminiMessages.length - 1];
      const result = await chat.sendMessageStream(lastMessage.parts);

      for await (const chunk of result.stream) {
        const text = chunk.text();
        if (text) {
          yield {
            content: text,
          };
        }

        // Check for function calls in chunk
        if (chunk.functionCalls && chunk.functionCalls.length > 0) {
          const toolCalls: ToolCall[] = chunk.functionCalls.map((funcCall: any) => ({
            id: `call_${Date.now()}_${Math.random().toString(36).substring(7)}`,
            function: {
              name: funcCall.name,
              arguments: JSON.stringify(funcCall.args || {}),
            },
          }));

          yield {
            content: '',
            toolCalls,
            finishReason: 'tool_calls',
          };
        }
      }

      yield {
        content: '',
        finishReason: 'stop',
      };
    } catch (error: any) {
      this.handleError(error);
    }
  }
}

