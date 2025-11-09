/**
 * Tests for Tool Executor
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ToolExecutor } from '../executor';
import { ToolSpec } from '../types';

describe('ToolExecutor', () => {
  let executor: ToolExecutor;
  let mockHandler: ReturnType<typeof vi.fn>;

  const sampleToolSpec: ToolSpec = {
    name: 'createUser',
    description: 'Create a new user',
    operationId: 'createUser',
    jsonSchema: {
      type: 'object',
      properties: {
        email: {
          type: 'string',
          format: 'email',
        },
        password: {
          type: 'string',
          minLength: 8,
        },
        name: {
          type: 'string',
        },
      },
      required: ['email', 'password'],
    },
  };

  beforeEach(() => {
    executor = new ToolExecutor({
      enableRateLimit: true,
      enableSanitization: true,
      enableAuditLog: false, // Disable for tests unless needed
    });
    mockHandler = vi.fn().mockResolvedValue({ success: true, userId: '123' });
  });

  describe('register', () => {
    it('should register a tool handler', () => {
      executor.register('createUser', mockHandler);
      expect(executor.hasHandler('createUser')).toBe(true);
    });

    it('should throw error if handler already exists', () => {
      executor.register('createUser', mockHandler);
      expect(() => {
        executor.register('createUser', mockHandler);
      }).toThrow('already registered');
    });
  });

  describe('execute', () => {
    it('should execute tool successfully', async () => {
      executor.register('createUser', mockHandler);

      const result = await executor.execute(
        sampleToolSpec,
        {
          email: 'test@example.com',
          password: 'password123',
        }
      );

      expect(result.success).toBe(true);
      expect(result.result).toBeDefined();
      expect(mockHandler).toHaveBeenCalled();
    });

    it('should validate inputs against schema', async () => {
      executor.register('createUser', mockHandler);

      // Missing required field
      const result1 = await executor.execute(
        sampleToolSpec,
        { email: 'test@example.com' }
      );

      expect(result1.success).toBe(false);
      expect(result1.error).toContain('validation failed');
      expect(mockHandler).not.toHaveBeenCalled();

      // Invalid email format
      const result2 = await executor.execute(
        sampleToolSpec,
        { email: 'invalid-email', password: 'password123' }
      );

      expect(result2.success).toBe(false);
      expect(result2.error).toContain('validation failed');
    });

    it('should return error if handler not found', async () => {
      const result = await executor.execute(
        sampleToolSpec,
        { email: 'test@example.com', password: 'password123' }
      );

      expect(result.success).toBe(false);
      expect(result.error).toContain('handler not found');
    });

    it('should handle handler errors', async () => {
      const errorHandler = vi.fn().mockRejectedValue(new Error('Handler error'));
      executor.register('createUser', errorHandler);

      const result = await executor.execute(
        sampleToolSpec,
        { email: 'test@example.com', password: 'password123' }
      );

      expect(result.success).toBe(false);
      expect(result.error).toContain('Handler error');
    });

    it('should sanitize inputs', async () => {
      executor.register('createUser', mockHandler);

      await executor.execute(
        sampleToolSpec,
        {
          email: 'test@example.com',
          password: 'password123',
          name: '<script>alert("xss")</script>',
        }
      );

      const callArgs = mockHandler.mock.calls[0][0];
      expect(callArgs.name).not.toContain('<script>');
    });

    it('should track execution time', async () => {
      executor.register('createUser', mockHandler);

      const result = await executor.execute(
        sampleToolSpec,
        { email: 'test@example.com', password: 'password123' }
      );

      expect(result.executionTimeMs).toBeGreaterThanOrEqual(0);
    });
  });

  describe('rate limiting', () => {
    it('should enforce rate limits', async () => {
      const limitedExecutor = new ToolExecutor({
        enableRateLimit: true,
        defaultRateLimit: 2, // 2 requests per minute
      });

      limitedExecutor.register('createUser', mockHandler);

      // First two should succeed
      const result1 = await limitedExecutor.execute(
        sampleToolSpec,
        { email: 'test1@example.com', password: 'password123' }
      );
      expect(result1.success).toBe(true);

      const result2 = await limitedExecutor.execute(
        sampleToolSpec,
        { email: 'test2@example.com', password: 'password123' }
      );
      expect(result2.success).toBe(true);

      // Third should be rate limited
      const result3 = await limitedExecutor.execute(
        sampleToolSpec,
        { email: 'test3@example.com', password: 'password123' }
      );
      expect(result3.success).toBe(false);
      expect(result3.error).toContain('Rate limit exceeded');
    });

    it('should respect tool-specific rate limits', async () => {
      const limitedExecutor = new ToolExecutor({
        enableRateLimit: true,
        defaultRateLimit: 100,
        rateLimits: new Map([['createUser', 1]]),
      });

      limitedExecutor.register('createUser', mockHandler);

      const result1 = await limitedExecutor.execute(
        sampleToolSpec,
        { email: 'test1@example.com', password: 'password123' }
      );
      expect(result1.success).toBe(true);

      const result2 = await limitedExecutor.execute(
        sampleToolSpec,
        { email: 'test2@example.com', password: 'password123' }
      );
      expect(result2.success).toBe(false);
      expect(result2.error).toContain('Rate limit exceeded');
    });
  });

  describe('getStats', () => {
    it('should return executor statistics', () => {
      executor.register('createUser', mockHandler);
      executor.register('updateUser', mockHandler);

      const stats = executor.getStats();
      expect(stats.registeredTools).toBe(2);
    });
  });

  describe('unregister', () => {
    it('should unregister a tool handler', () => {
      executor.register('createUser', mockHandler);
      expect(executor.hasHandler('createUser')).toBe(true);

      executor.unregister('createUser');
      expect(executor.hasHandler('createUser')).toBe(false);
    });
  });
});

