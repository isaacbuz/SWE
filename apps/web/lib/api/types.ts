/**
 * API types
 */

export interface ToolSpec {
  name: string;
  description: string;
  operationId: string;
  endpoint?: string;
  method?: string;
  tags?: string[];
  jsonSchema?: object;
}

export interface ToolExecuteRequest {
  toolName: string;
  arguments: Record<string, unknown>;
  options?: Record<string, unknown>;
}

export interface ToolExecuteResponse {
  success: boolean;
  result?: unknown;
  error?: string;
  executionTime: number;
  toolName: string;
  timestamp: string;
}

export interface ToolListResponse {
  tools: ToolSpec[];
  total: number;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  userId: string;
  toolName: string;
  success: boolean;
  durationMs: number;
  error?: string;
}

export interface AuditLogResponse {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  pageSize: number;
}
