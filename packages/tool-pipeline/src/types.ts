/**
 * Tool Calling Pipeline Types
 */

export interface ToolCall {
  /** Tool name (operationId) */
  name: string;
  
  /** Tool arguments */
  arguments: Record<string, unknown>;
  
  /** Call ID for tracking */
  id?: string;
}

export interface ToolResult {
  /** Tool name */
  name: string;
  
  /** Execution result */
  result: unknown;
  
  /** Whether execution was successful */
  success: boolean;
  
  /** Error message if failed */
  error?: string;
  
  /** Execution time in milliseconds */
  executionTimeMs: number;
  
  /** Call ID */
  callId?: string;
}

export interface LLMMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  toolCalls?: ToolCall[];
  toolCallId?: string;
}

export interface LLMCompletion {
  content: string;
  toolCalls?: ToolCall[];
  usage?: {
    inputTokens: number;
    outputTokens: number;
  };
}

export interface ToolCallingOptions {
  /** Maximum number of tool calling turns */
  maxTurns?: number;
  
  /** Whether to stop on first tool call */
  stopOnFirstToolCall?: boolean;
  
  /** Timeout per turn in milliseconds */
  timeoutPerTurn?: number;
  
  /** Whether to validate tool results */
  validateResults?: boolean;
}

export interface ToolCallingContext {
  /** Conversation messages */
  messages: LLMMessage[];
  
  /** System prompt */
  systemPrompt?: string;
  
  /** Tool execution results */
  toolResults: ToolResult[];
  
  /** Current turn number */
  turn: number;
  
  /** Metadata */
  metadata?: Record<string, unknown>;
}

