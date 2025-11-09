/**
 * Type definitions for Tool Calling Pipeline
 */

export interface ToolCall {
  /** Tool name/ID */
  name: string;
  
  /** Tool arguments */
  arguments: Record<string, any>;
  
  /** Call ID for tracking */
  id?: string;
}

export interface ToolCallResult {
  /** Tool call ID */
  callId: string;
  
  /** Tool name */
  toolName: string;
  
  /** Execution result */
  result: any;
  
  /** Error if execution failed */
  error?: string;
  
  /** Execution metadata */
  metadata?: {
    executionTimeMs: number;
    tokensUsed?: number;
    cost?: number;
  };
}

export interface PipelineMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  toolCalls?: ToolCall[];
  toolCallResults?: ToolCallResult[];
}

export interface PipelineResult {
  /** Final response content */
  content: string;
  
  /** All tool calls made during execution */
  toolCalls: ToolCallResult[];
  
  /** Total execution time */
  executionTimeMs: number;
  
  /** Number of turns taken */
  turns: number;
  
  /** Final model response */
  modelResponse: any;
  
  /** Metadata */
  metadata: {
    tokensUsed?: number;
    cost?: number;
    modelUsed?: string;
  };
}

export interface PipelineOptions {
  /** Maximum number of tool calling turns */
  maxTurns?: number;
  
  /** Enable verbose logging */
  verbose?: boolean;
  
  /** Custom tool call handler */
  onToolCall?: (call: ToolCall) => void | Promise<void>;
  
  /** Custom result handler */
  onToolResult?: (result: ToolCallResult) => void | Promise<void>;
}

