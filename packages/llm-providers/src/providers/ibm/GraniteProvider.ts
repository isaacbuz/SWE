/**
 * IBM Granite Provider Implementation
 * 
 * Implements the LLMProvider interface for IBM Granite models.
 */
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
 * IBM Granite Provider
 * 
 * Supports IBM Granite models via Watsonx.ai API
 * with tool calling (function calling) support.
 */
export class GraniteProvider implements LLMProvider {
  readonly name = 'ibm:granite-13b-chat-v2';
  readonly maxContext = 4_096; // Granite models support up to 4K tokens
  readonly pricePerMTokIn = 0.75; // Example pricing for Granite
  readonly pricePerMTokOut = 0.75;
  readonly capabilities: ProviderCapabilities = {
    tools: true,
    vision: false, // Granite doesn't support vision yet
    streaming: true,
    jsonMode: false, // Granite doesn't have explicit JSON mode
  };

  private apiKey: string;
  private apiUrl: string;
  private defaultModel: string;

  constructor(
    apiKey: string,
    apiUrl: string = 'https://us-south.ml.cloud.ibm.com',
    defaultModel: string = 'granite-13b-chat-v2'
  ) {
    if (!apiKey) {
      throw new AuthenticationError('IBM API key is required');
    }

    this.apiKey = apiKey;
    this.apiUrl = apiUrl;
    this.defaultModel = defaultModel;
    this.name = `ibm:${defaultModel}`;
  }

  /**
   * Convert messages to IBM Granite format
   */
  private convertMessages(messages: Message[]): any[] {
    const graniteMessages: any[] = [];

    for (const msg of messages) {
      if (msg.role === 'system') {
        // Granite uses system messages
        graniteMessages.push({
          role: 'system',
          content: msg.content,
        });
        continue;
      }

      if (msg.role === 'user' || msg.role === 'tool') {
        let content = msg.content || '';

        // Handle tool responses
        if (msg.role === 'tool' && msg.toolCallId) {
          content = `Tool result: ${content}`;
        }

        graniteMessages.push({
          role: 'user',
          content,
        });
      } else if (msg.role === 'assistant') {
        let content = msg.content || '';

        // Handle tool calls
        if (msg.toolCalls && msg.toolCalls.length > 0) {
          const toolCallTexts = msg.toolCalls.map((tc) => 
            `Calling tool ${tc.function.name} with args: ${tc.function.arguments}`
          );
          content = `${content}\n${toolCallTexts.join('\n')}`;
        }

        graniteMessages.push({
          role: 'assistant',
          content,
        });
      }
    }

    return graniteMessages;
  }

  /**
   * Convert ToolSpec to IBM Granite tool format
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
   * Convert IBM Granite response to CompletionResult
   */
  private convertResponse(
    response: any,
    model: string,
    promptTokens: number = 0,
    completionTokens: number = 0
  ): CompletionResult {
    const content = response.choices?.[0]?.message?.content || '';
    const toolCalls: ToolCall[] = [];

    // Extract tool calls from response
    if (response.choices?.[0]?.message?.tool_calls) {
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
    } else if (response.choices?.[0]?.finish_reason === 'length') {
      finishReason = 'length';
    } else if (response.choices?.[0]?.finish_reason === 'content_filter') {
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
        'IBM API rate limit exceeded',
        error.retryAfter || 60
      );
    }

    if (error.status === 401 || error.status === 403) {
      throw new AuthenticationError('Invalid IBM API key');
    }

    if (error.status === 400) {
      throw new InvalidRequestError(error.message || 'Invalid request');
    }

    if (error.status === 404) {
      throw new ModelNotFoundError(`Model not found: ${this.defaultModel}`);
    }

    throw new LLMProviderError(
      `IBM API error: ${error.message || 'Unknown error'}`,
      error
    );
  }

  /**
   * Make API request to IBM Watsonx.ai
   */
  private async makeRequest(endpoint: string, body: any): Promise<any> {
    const url = `${this.apiUrl}${endpoint}`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw {
        status: response.status,
        message: error.message || `HTTP ${response.status}`,
      };
    }

    return response.json();
  }

  /**
   * Complete a chat completion request
   */
  async completion(opts: ExtendedCompletionOptions): Promise<CompletionResult> {
    try {
      const modelName = opts.model || this.defaultModel;

      // Convert messages
      const graniteMessages = this.convertMessages(opts.messages);

      // Prepare request body
      const body: any = {
        model_id: modelName,
        input: graniteMessages,
        parameters: {
          temperature: opts.temperature ?? 0.7,
          max_new_tokens: opts.maxTokens,
        },
      };

      // Add tools if provided
      if (opts.tools && opts.tools.length > 0) {
        body.tools = this.convertTools(opts.tools);
      }

      // Call IBM API
      const response = await this.makeRequest('/ml/v1/text/chat', body);

      // Estimate tokens if not provided
      const promptText = opts.messages.map((m) => m.content).join('\n');
      const promptTokens = response.usage?.prompt_tokens || this.estimateTokens(promptText);
      const completionTokens = response.usage?.completion_tokens || this.estimateTokens(response.choices?.[0]?.message?.content || '');

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
      const graniteMessages = this.convertMessages(opts.messages);

      // Prepare request body
      const body: any = {
        model_id: modelName,
        input: graniteMessages,
        parameters: {
          temperature: opts.temperature ?? 0.7,
          max_new_tokens: opts.maxTokens,
          stream: true,
        },
      };

      // Add tools if provided
      if (opts.tools && opts.tools.length > 0) {
        body.tools = this.convertTools(opts.tools);
      }

      // Stream response
      const url = `${this.apiUrl}/ml/v1/text/chat`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: response.statusText }));
        throw {
          status: response.status,
          message: error.message || `HTTP ${response.status}`,
        };
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Stream not available');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let toolCalls: ToolCall[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
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
              return;
            }

            try {
              const chunk = JSON.parse(data);
              if (chunk.choices?.[0]?.delta?.content) {
                yield {
                  content: chunk.choices[0].delta.content,
                };
              }

              // Check for tool calls
              if (chunk.choices?.[0]?.delta?.tool_calls) {
                for (const toolCall of chunk.choices[0].delta.tool_calls) {
                  const existingCall = toolCalls.find((tc) => tc.id === toolCall.id);
                  if (existingCall) {
                    const currentArgs = JSON.parse(existingCall.function.arguments);
                    const newArgs = { ...currentArgs, ...toolCall.function.arguments };
                    existingCall.function.arguments = JSON.stringify(newArgs);
                  } else {
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
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error: any) {
      this.handleError(error);
    }
  }
}

