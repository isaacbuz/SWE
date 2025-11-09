import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ToolCallingPipeline } from '../../src/ToolCallingPipeline';
import { ToolRegistry } from '@ai-company/openapi-tools';
import { ToolExecutor } from '@ai-company/tool-executor';
import { OpenAIProvider } from '@ai-company/llm-providers';
import { ToolSpec } from '@ai-company/openapi-tools';

describe('ToolCallingPipeline Integration Tests', () => {
  let pipeline: ToolCallingPipeline;
  let registry: ToolRegistry;
  let executor: ToolExecutor;
  let provider: OpenAIProvider;

  beforeEach(() => {
    registry = new ToolRegistry();
    executor = new ToolExecutor();
    provider = new OpenAIProvider('test-key', 'gpt-4-turbo-preview');
    pipeline = new ToolCallingPipeline(registry, executor, provider);
  });

  it('should execute pipeline with single tool call', async () => {
    // Mock tool spec
    const toolSpec: ToolSpec = {
      name: 'testTool',
      description: 'Test tool',
      jsonSchema: {
        type: 'object',
        properties: {
          input: { type: 'string' },
        },
        required: ['input'],
      },
      operationId: 'testTool',
    };

    // Register tool
    await registry.loadSpecs([]);
    executor.registerTool(toolSpec, async (args) => {
      return { result: `Processed: ${(args as any).input}` };
    });

    // Mock provider completion
    vi.spyOn(provider, 'completion').mockResolvedValue({
      content: 'Tool executed successfully',
      toolCalls: undefined,
      usage: {
        promptTokens: 100,
        completionTokens: 50,
        totalTokens: 150,
      },
      finishReason: 'stop',
    });

    const result = await pipeline.executeWithTools(
      'Execute testTool with input "hello"',
      ['testTool'],
      { maxTurns: 1 }
    );

    expect(result.content).toBe('Tool executed successfully');
    expect(result.turns).toBe(1);
  });

  it('should handle multi-turn tool calling', async () => {
    const toolSpec: ToolSpec = {
      name: 'multiStepTool',
      description: 'Multi-step tool',
      jsonSchema: {
        type: 'object',
        properties: {
          step: { type: 'string' },
        },
        required: ['step'],
      },
      operationId: 'multiStepTool',
    };

    executor.registerTool(toolSpec, async (args) => {
      return { step: (args as any).step, completed: true };
    });

    let callCount = 0;
    vi.spyOn(provider, 'completion').mockImplementation(async () => {
      callCount++;
      if (callCount === 1) {
        return {
          content: '',
          toolCalls: [
            {
              id: 'call-1',
              type: 'function',
              function: {
                name: 'multiStepTool',
                arguments: JSON.stringify({ step: 'step1' }),
              },
            },
          ],
          usage: {
            promptTokens: 100,
            completionTokens: 50,
            totalTokens: 150,
          },
          finishReason: 'tool_calls',
        };
      } else {
        return {
          content: 'All steps completed',
          toolCalls: undefined,
          usage: {
            promptTokens: 100,
            completionTokens: 50,
            totalTokens: 150,
          },
          finishReason: 'stop',
        };
      }
    });

    const result = await pipeline.executeWithTools(
      'Execute multi-step process',
      ['multiStepTool'],
      { maxTurns: 5 }
    );

    expect(result.content).toBe('All steps completed');
    expect(result.turns).toBe(2);
    expect(callCount).toBe(2);
  });

  it('should handle tool execution errors gracefully', async () => {
    const toolSpec: ToolSpec = {
      name: 'errorTool',
      description: 'Tool that errors',
      jsonSchema: {
        type: 'object',
        properties: {},
      },
      operationId: 'errorTool',
    };

    executor.registerTool(toolSpec, async () => {
      throw new Error('Tool execution failed');
    });

    vi.spyOn(provider, 'completion').mockResolvedValue({
      content: '',
      toolCalls: [
        {
          id: 'call-1',
          type: 'function',
          function: {
            name: 'errorTool',
            arguments: JSON.stringify({}),
          },
        },
      ],
      usage: {
        promptTokens: 100,
        completionTokens: 50,
        totalTokens: 150,
      },
      finishReason: 'tool_calls',
    });

    // Second call should handle error
    vi.spyOn(provider, 'completion').mockResolvedValueOnce({
      content: '',
      toolCalls: [
        {
          id: 'call-1',
          type: 'function',
          function: {
            name: 'errorTool',
            arguments: JSON.stringify({}),
          },
        },
      ],
      usage: {
        promptTokens: 100,
        completionTokens: 50,
        totalTokens: 150,
      },
      finishReason: 'tool_calls',
    }).mockResolvedValueOnce({
      content: 'Error handled, retrying',
      toolCalls: undefined,
      usage: {
        promptTokens: 100,
        completionTokens: 50,
        totalTokens: 150,
      },
      finishReason: 'stop',
    });

    const result = await pipeline.executeWithTools(
      'Execute errorTool',
      ['errorTool'],
      { maxTurns: 5 }
    );

    expect(result.executionResults).toBeDefined();
    expect(result.executionResults?.some((r) => !r.success)).toBe(true);
  });

  it('should enforce max turns limit', async () => {
    const toolSpec: ToolSpec = {
      name: 'infiniteTool',
      description: 'Tool that causes infinite loop',
      jsonSchema: {
        type: 'object',
        properties: {},
      },
      operationId: 'infiniteTool',
    };

    executor.registerTool(toolSpec, async () => {
      return { result: 'done' };
    });

    // Always return tool calls to simulate infinite loop
    vi.spyOn(provider, 'completion').mockResolvedValue({
      content: '',
      toolCalls: [
        {
          id: 'call-1',
          type: 'function',
          function: {
            name: 'infiniteTool',
            arguments: JSON.stringify({}),
          },
        },
      ],
      usage: {
        promptTokens: 100,
        completionTokens: 50,
        totalTokens: 150,
      },
      finishReason: 'tool_calls',
    });

    await expect(
      pipeline.executeWithTools('Execute infiniteTool', ['infiniteTool'], {
        maxTurns: 2,
      })
    ).rejects.toThrow('Max turns');
  });
});

