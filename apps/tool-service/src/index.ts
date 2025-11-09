/**
 * Tool Execution HTTP Service
 * 
 * Provides HTTP API for tool execution that bridges TypeScript packages
 * with the Python FastAPI backend.
 */
import express from 'express';
import cors from 'cors';
import { ToolRegistry } from '@ai-company/openapi-tools';
import { ToolExecutor } from '@ai-company/tool-executor';
import { AuditLogger } from '@ai-company/audit-logging';
import { PermissionChecker } from '@ai-company/permissions';
import { RateLimiter } from '@ai-company/rate-limiting';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Initialize services
const toolRegistry = new ToolRegistry();
const toolExecutor = new ToolExecutor(toolRegistry);
const auditLogger = new AuditLogger();
const permissionChecker = new PermissionChecker();
const rateLimiter = new RateLimiter();

// Load tool specs on startup
async function initialize() {
  try {
    await toolRegistry.loadSpecs([
      './tools/openapi/ai-dev-tools.yaml',
    ]);
    console.log('Tool registry initialized');
  } catch (error) {
    console.error('Failed to initialize tool registry:', error);
    process.exit(1);
  }
}

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'tool-service',
    timestamp: new Date().toISOString(),
  });
});

// List tools
app.get('/tools', async (req, res) => {
  try {
    const tools = toolRegistry.getToolSpecs();
    const tag = req.query.tag as string | undefined;
    const search = req.query.search as string | undefined;

    let filteredTools = tools;

    if (tag) {
      filteredTools = filteredTools.filter((tool) =>
        tool.tags?.includes(tag)
      );
    }

    if (search) {
      const searchLower = search.toLowerCase();
      filteredTools = filteredTools.filter(
        (tool) =>
          tool.name.toLowerCase().includes(searchLower) ||
          tool.description.toLowerCase().includes(searchLower)
      );
    }

    res.json({
      tools: filteredTools.map((tool) => ({
        name: tool.name,
        description: tool.description,
        operationId: tool.operationId,
        endpoint: tool.endpoint,
        method: 'POST', // Default for now
        tags: tool.tags,
      })),
      total: filteredTools.length,
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get tool details
app.get('/tools/:name', async (req, res) => {
  try {
    const tool = toolRegistry.getToolByName(req.params.name);
    if (!tool) {
      return res.status(404).json({ error: 'Tool not found' });
    }

    res.json({
      name: tool.name,
      description: tool.description,
      operationId: tool.operationId,
      endpoint: tool.endpoint,
      method: 'POST',
      tags: tool.tags,
      jsonSchema: tool.jsonSchema,
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Execute tool
app.post('/tools/execute', async (req, res) => {
  const startTime = Date.now();

  try {
    const { toolName, arguments: args, userId, options } = req.body;

    if (!toolName || !args) {
      return res.status(400).json({
        error: 'toolName and arguments are required',
      });
    }

    // Check permissions
    if (userId) {
      const hasPermission = permissionChecker.hasPermission(
        userId,
        toolName,
        'execute'
      );
      if (!hasPermission) {
        return res.status(403).json({ error: 'Permission denied' });
      }
    }

    // Check rate limits
    if (userId) {
      const rateStatus = rateLimiter.checkLimit({
        maxRequests: 100,
        windowMs: 60000,
        identifier: userId,
      });
      if (rateStatus.exceeded) {
        return res.status(429).json({
          error: 'Rate limit exceeded',
          resetAt: rateStatus.resetAt,
        });
      }
    }

    // Execute tool
    const result = await toolExecutor.execute(toolName, args);

    const durationMs = Date.now() - startTime;

    // Audit logging
    if (userId) {
      await auditLogger.logExecution(
        userId,
        toolName,
        args,
        result.success ? result.data : undefined,
        result.success,
        durationMs,
        result.success ? undefined : result.error?.message,
        {
          ipAddress: req.ip,
          userAgent: req.get('user-agent'),
        }
      );
    }

    if (!result.success) {
      return res.status(500).json({
        success: false,
        error: result.error?.message || 'Tool execution failed',
      });
    }

    res.json({
      success: true,
      result: result.data,
      executionTime: durationMs,
      toolName,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    const durationMs = Date.now() - startTime;
    res.status(500).json({
      success: false,
      error: error.message,
      executionTime: durationMs,
    });
  }
});

// Get audit logs
app.get('/tools/audit', async (req, res) => {
  try {
    const {
      userId,
      toolName,
      startDate,
      endDate,
      page = '1',
      pageSize = '50',
    } = req.query;

    const logs = await auditLogger.queryLogs({
      userId: userId as string | undefined,
      toolName: toolName as string | undefined,
      startDate: startDate ? new Date(startDate as string) : undefined,
      endDate: endDate ? new Date(endDate as string) : undefined,
      limit: parseInt(pageSize as string, 10),
      offset: (parseInt(page as string, 10) - 1) * parseInt(pageSize as string, 10),
    });

    res.json({
      logs: logs.map((log) => ({
        id: log.id,
        timestamp: log.timestamp,
        userId: log.userId,
        toolName: log.toolName,
        success: log.success,
        durationMs: log.durationMs,
        error: log.error,
      })),
      total: logs.length,
      page: parseInt(page as string, 10),
      pageSize: parseInt(pageSize as string, 10),
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
async function start() {
  await initialize();

  app.listen(PORT, () => {
    console.log(`Tool service running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
  });
}

start().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

