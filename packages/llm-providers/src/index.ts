/**
 * @ai-company/llm-providers
 * 
 * Provider-agnostic LLM interface for TypeScript/Node.js
 */

export type {
  MessageRole,
  Message,
  ToolSpec,
  ToolCall,
  CompletionChunk,
  CompletionOptions,
  Usage,
  CompletionResult,
  ProviderCapabilities,
  LLMProvider,
} from './domain/LLMProvider';

export {
  LLMProviderError,
  RateLimitError,
  AuthenticationError,
  InvalidRequestError,
  ModelNotFoundError,
} from './domain/LLMProvider';

// Provider implementations
export { OpenAIProvider } from './providers/openai';
export { AnthropicProvider } from './providers/anthropic';

