/**
 * Provider-agnostic LLM interface
 * 
 * This interface enables the MoE router to work with any LLM provider
 * (OpenAI, Anthropic, Google, etc.) through a unified API.
 */

/**
 * Message role in conversation
 */
export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

/**
 * Message in conversation
 */
export interface Message {
  role: MessageRole;
  content: string;
  toolCalls?: ToolCall[];
  toolCallId?: string;
}

/**
 * Tool specification for function calling
 */
export interface ToolSpec {
  name: string;
  description: string;
  jsonSchema: object; // JSON Schema for parameters
}

/**
 * Tool call made by the model
 */
export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string; // JSON string
  };
}

/**
 * Completion chunk for streaming
 */
export interface CompletionChunk {
  content: string;
  finishReason?: 'stop' | 'length' | 'tool_calls' | 'content_filter';
  toolCalls?: ToolCall[];
}

/**
 * Completion options
 */
export interface CompletionOptions {
  system?: string;
  messages: Message[];
  tools?: ToolSpec[];
  temperature?: number;
  maxTokens?: number;
  responseFormat?: 'text' | 'json_object';
  stopSequences?: string[];
}

/**
 * Token usage statistics
 */
export interface Usage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  cacheCreationTokens?: number;
  cacheReadTokens?: number;
}

/**
 * Completion result
 */
export interface CompletionResult {
  content: string;
  toolCalls?: ToolCall[];
  usage: Usage;
  finishReason: 'stop' | 'length' | 'tool_calls' | 'content_filter';
  model?: string;
}

/**
 * Provider capabilities
 */
export interface ProviderCapabilities {
  tools: boolean;        // Function/tool calling support
  vision: boolean;      // Image/video input support
  streaming: boolean;   // Streaming responses
  jsonMode: boolean;    // Guaranteed JSON output
}

/**
 * LLM Provider interface
 * 
 * All LLM providers (OpenAI, Anthropic, etc.) must implement this interface.
 */
export interface LLMProvider {
  /**
   * Provider identifier (e.g., "openai:gpt-4")
   */
  readonly name: string;

  /**
   * Maximum context window size
   */
  readonly maxContext: number;

  /**
   * Price per million input tokens (USD)
   */
  readonly pricePerMTokIn: number;

  /**
   * Price per million output tokens (USD)
   */
  readonly pricePerMTokOut: number;

  /**
   * Provider capabilities
   */
  readonly capabilities: ProviderCapabilities;

  /**
   * Generate a completion
   * 
   * @param opts - Completion options
   * @returns Completion result
   */
  completion(opts: CompletionOptions): Promise<CompletionResult>;

  /**
   * Generate a streaming completion
   * 
   * @param opts - Completion options
   * @returns Async iterable of completion chunks
   */
  streamCompletion(opts: CompletionOptions): AsyncIterable<CompletionChunk>;
}

/**
 * Provider error types
 */
export class LLMProviderError extends Error {
  constructor(message: string, public readonly code?: string) {
    super(message);
    this.name = 'LLMProviderError';
  }
}

export class RateLimitError extends LLMProviderError {
  constructor(
    message: string,
    public readonly retryAfter?: number
  ) {
    super(message, 'RATE_LIMIT');
    this.name = 'RateLimitError';
  }
}

export class AuthenticationError extends LLMProviderError {
  constructor(message: string) {
    super(message, 'AUTHENTICATION');
    this.name = 'AuthenticationError';
  }
}

export class InvalidRequestError extends LLMProviderError {
  constructor(message: string) {
    super(message, 'INVALID_REQUEST');
    this.name = 'InvalidRequestError';
  }
}

export class ModelNotFoundError extends LLMProviderError {
  constructor(message: string) {
    super(message, 'MODEL_NOT_FOUND');
    this.name = 'ModelNotFoundError';
  }
}

