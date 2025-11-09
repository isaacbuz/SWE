#!/usr/bin/env node

/**
 * Spec to GitHub Issues CLI Tool
 * 
 * Reads a specification file and uses the tool calling pipeline to create
 * GitHub issues from it.
 */

import { readFile } from 'fs/promises';
import { resolve } from 'path';
import { Command } from 'commander';
import { ToolRegistry } from '@ai-company/openapi-tools';
import { ToolExecutor } from '@ai-company/tool-executor';
import { ToolCallingPipeline } from '@ai-company/tool-pipeline';
import { OpenAIProvider } from '@ai-company/llm-providers';
import { ToolSpec } from '@ai-company/openapi-tools';

const program = new Command();

program
  .name('spec-to-github')
  .description('Convert a specification file into GitHub issues using AI')
  .version('0.1.0')
  .requiredOption('-s, --spec <path>', 'Path to specification file')
  .requiredOption('-o, --owner <owner>', 'GitHub repository owner')
  .requiredOption('-r, --repo <repo>', 'GitHub repository name')
  .option('-t, --token <token>', 'GitHub personal access token', process.env.GITHUB_TOKEN)
  .option('--openai-key <key>', 'OpenAI API key', process.env.OPENAI_API_KEY)
  .option('--anthropic-key <key>', 'Anthropic API key', process.env.ANTHROPIC_API_KEY)
  .option('--provider <provider>', 'LLM provider to use', 'openai')
  .option('--model <model>', 'Model to use', 'gpt-4-turbo-preview')
  .option('--max-turns <turns>', 'Maximum tool calling turns', '5')
  .parse(process.argv);

interface SpecToGithubOptions {
  spec: string;
  owner: string;
  repo: string;
  token?: string;
  openaiKey?: string;
  anthropicKey?: string;
  provider: string;
  model: string;
  maxTurns: string;
}

async function main() {
  const opts = program.opts<SpecToGithubOptions>();

  // Validate inputs
  if (!opts.token) {
    console.error('Error: GitHub token required (--token or GITHUB_TOKEN env var)');
    process.exit(1);
  }

  const apiKey = opts.provider === 'openai' ? opts.openaiKey : opts.anthropicKey;
  if (!apiKey) {
    console.error(`Error: ${opts.provider} API key required`);
    process.exit(1);
  }

  try {
    console.log('📋 Loading specification...');
    const specPath = resolve(opts.spec);
    const spec = await readFile(specPath, 'utf-8');

    console.log('🔧 Initializing components...');
    
    // Initialize tool registry
    const registry = new ToolRegistry();
    await registry.loadSpecs(['./tools/openapi/ai-dev-tools.yaml']);

    // Initialize tool executor
    const executor = new ToolExecutor();
    
    // Register GitHub createIssues tool handler
    const createIssuesTool = registry.getToolByName('createIssues');
    if (createIssuesTool) {
      executor.registerTool(createIssuesTool, async (args: unknown) => {
        const { owner, repo, tasks } = args as {
          owner: string;
          repo: string;
          tasks: Array<{
            title: string;
            body: string;
            labels?: string[];
            assignees?: string[];
            milestone?: string;
          }>;
        };

        // In a real implementation, this would call the GitHub API
        // For now, we'll simulate it
        console.log(`\n📝 Creating ${tasks.length} issues in ${owner}/${repo}:`);
        const issues = tasks.map((task, index) => {
          console.log(`  ${index + 1}. ${task.title}`);
          return {
            number: 100 + index,
            url: `https://github.com/${owner}/${repo}/issues/${100 + index}`,
            title: task.title,
          };
        });

        return { issues };
      });
    }

    // Initialize LLM provider
    let provider;
    if (opts.provider === 'openai') {
      provider = new OpenAIProvider(apiKey!, opts.model);
    } else if (opts.provider === 'anthropic') {
      const { AnthropicProvider } = await import('@ai-company/llm-providers');
      provider = new AnthropicProvider(apiKey!, opts.model);
    } else {
      throw new Error(`Unsupported provider: ${opts.provider}`);
    }

    // Initialize pipeline
    const pipeline = new ToolCallingPipeline(registry, executor, provider);

    console.log('🤖 Analyzing specification and creating issues...\n');

    // Build prompt
    const prompt = `You are a technical project planner. Analyze the following specification and break it down into well-structured GitHub issues.

Repository: ${opts.owner}/${opts.repo}

Specification:
${spec}

Use the createIssues tool to create the issues. Each issue should have:
- Clear, concise title
- Detailed description with acceptance criteria
- Appropriate labels (e.g., enhancement, bug, documentation)
- Dependencies noted in the description

Break down the specification into logical, actionable issues.`;

    // Execute pipeline
    const result = await pipeline.executeWithTools(
      prompt,
      ['createIssues'],
      {
        maxTurns: parseInt(opts.maxTurns, 10),
        parallelExecution: false,
      }
    );

    // Display results
    console.log('\n✅ Pipeline completed successfully!\n');
    console.log(`📊 Summary:`);
    console.log(`   - Turns: ${result.turns}`);
    console.log(`   - Cost: $${result.cost?.toFixed(4) || '0.0000'}`);
    
    if (result.executionResults) {
      const successful = result.executionResults.filter((r) => r.success).length;
      console.log(`   - Tools executed: ${successful}/${result.executionResults.length}`);
    }

    console.log(`\n💬 Final response:\n${result.content}\n`);

  } catch (error) {
    console.error('\n❌ Error:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main();

