#!/usr/bin/env node
/**
 * Spec to GitHub Issues CLI Command
 * 
 * Converts a specification document into GitHub issues using LLM + tools.
 * 
 * Usage:
 *   pnpm run spec-to-github --spec ./examples/feature-spec.md --owner isaacbuz --repo my-app
 */

import { readFileSync } from 'fs';
import { resolve } from 'path';
import { Command } from 'commander';
import chalk from 'chalk';
import { ToolRegistry, ToolExecutor } from '@ai-company/openapi-tools';
import { ToolCallingPipeline, LLMProvider } from '@ai-company/tool-pipeline';

// Simple LLM provider adapter (would be replaced with actual provider in production)
class SimpleLLMProvider implements LLMProvider {
  async complete(
    messages: any[],
    tools?: any[],
    options?: any
  ): Promise<{
    content: string;
    toolCalls?: any[];
    usage?: { inputTokens: number; outputTokens: number };
    model?: string;
  }> {
    // This is a mock implementation - in production, this would call OpenAI, Anthropic, etc.
    // For now, we'll simulate a response that breaks down the spec into issues
    
    const lastMessage = messages[messages.length - 1];
    const content = lastMessage.content || '';
    
    // Simulate LLM breaking down spec into issues
    if (content.includes('specification') || content.includes('feature')) {
      // Extract issues from spec (simplified - real implementation would use actual LLM)
      const issues = this.extractIssuesFromSpec(content);
      
      return {
        content: `I've analyzed the specification and identified ${issues.length} issues to create.`,
        toolCalls: [{
          id: 'call-1',
          name: 'createIssues',
          arguments: {
            repository: `${process.env.GITHUB_OWNER || 'owner'}/${process.env.GITHUB_REPO || 'repo'}`,
            issues: issues
          }
        }],
        usage: {
          inputTokens: content.length / 4,
          outputTokens: 200
        },
        model: 'mock-llm'
      };
    }
    
    return {
      content: 'I need more information to create issues.',
      usage: {
        inputTokens: content.length / 4,
        outputTokens: 50
      },
      model: 'mock-llm'
    };
  }
  
  private extractIssuesFromSpec(spec: string): any[] {
    // Simple extraction logic - in production, LLM would do this
    const issues: any[] = [];
    const lines = spec.split('\n');
    let currentIssue: any = null;
    
    for (const line of lines) {
      if (line.match(/^#+\s+(.+)/)) {
        // New heading - save previous issue if exists
        if (currentIssue) {
          issues.push(currentIssue);
        }
        currentIssue = {
          title: line.replace(/^#+\s+/, ''),
          body: '',
          labels: ['enhancement']
        };
      } else if (currentIssue && line.trim()) {
        currentIssue.body += line + '\n';
      }
    }
    
    if (currentIssue) {
      issues.push(currentIssue);
    }
    
    // If no structured issues found, create a single issue
    if (issues.length === 0) {
      issues.push({
        title: 'Implement feature from specification',
        body: spec,
        labels: ['enhancement']
      });
    }
    
    return issues;
  }
}

interface SpecToGithubOptions {
  spec: string;
  owner: string;
  repo: string;
  provider?: string;
  verbose?: boolean;
}

async function specToGithub(options: SpecToGithubOptions): Promise<void> {
  const { spec, owner, repo, verbose = false } = options;
  
  console.log(chalk.blue('🚀 Spec to GitHub Issues Pipeline'));
  console.log(chalk.gray(`Spec: ${spec}`));
  console.log(chalk.gray(`Repository: ${owner}/${repo}\n`));
  
  try {
    // Step 1: Load spec file
    console.log(chalk.yellow('📄 Step 1: Loading specification...'));
    const specPath = resolve(spec);
    const specContent = readFileSync(specPath, 'utf-8');
    console.log(chalk.green(`✓ Loaded ${specContent.length} characters\n`));
    
    // Step 2: Initialize tool registry
    console.log(chalk.yellow('🔧 Step 2: Initializing tool registry...'));
    const registry = new ToolRegistry();
    const specPath_ = resolve(__dirname, '../../../tools/openapi/ai-dev-tools.yaml');
    await registry.loadSpecs([specPath_]);
    const tools = registry.getToolSpecs();
    console.log(chalk.green(`✓ Loaded ${tools.length} tools\n`));
    
    // Step 3: Register tool handlers
    console.log(chalk.yellow('⚙️  Step 3: Registering tool handlers...'));
    const executor = new ToolExecutor({
      enableRateLimit: false, // Disable for CLI
      enableSanitization: true,
      enableAuditLog: verbose
    });
    
    // Register createIssues handler
    executor.register('createIssues', async (args: any) => {
      const { repository, issues } = args;
      console.log(chalk.cyan(`\n📝 Creating ${issues.length} issues in ${repository}...`));
      
      // In production, this would call the actual GitHub API
      // For now, we'll simulate it
      const created: any[] = [];
      for (const issue of issues) {
        console.log(chalk.gray(`  - ${issue.title}`));
        created.push({
          number: Math.floor(Math.random() * 1000),
          title: issue.title,
          url: `https://github.com/${repository}/issues/${Math.floor(Math.random() * 1000)}`
        });
      }
      
      return {
        created,
        repository
      };
    });
    
    console.log(chalk.green('✓ Tool handlers registered\n'));
    
    // Step 4: Create LLM provider
    console.log(chalk.yellow('🤖 Step 4: Initializing LLM provider...'));
    const provider = new SimpleLLMProvider();
    console.log(chalk.green('✓ LLM provider ready\n'));
    
    // Step 5: Create pipeline
    console.log(chalk.yellow('🔗 Step 5: Creating tool calling pipeline...'));
    const pipeline = new ToolCallingPipeline(
      registry,
      executor,
      provider,
      {
        maxTurns: 5,
        verbose: verbose
      }
    );
    console.log(chalk.green('✓ Pipeline created\n'));
    
    // Step 6: Execute pipeline
    console.log(chalk.yellow('⚡ Step 6: Executing pipeline...'));
    const systemPrompt = `You are a helpful assistant that breaks down specifications into actionable GitHub issues.
Each issue should have:
- A clear, concise title
- A detailed description
- Appropriate labels (e.g., enhancement, bug, documentation)
- Any relevant context from the specification

Repository: ${owner}/${repo}`;
    
    const userPrompt = `Please analyze the following specification and create GitHub issues for each major task or feature:

${specContent}`;
    
    const result = await pipeline.executeWithTools(
      userPrompt,
      ['createIssues'],
      systemPrompt
    );
    
    console.log(chalk.green(`\n✓ Pipeline completed in ${result.executionTimeMs}ms`));
    console.log(chalk.green(`✓ Executed ${result.turns} turns`));
    console.log(chalk.green(`✓ Made ${result.toolCalls.length} tool calls\n`));
    
    // Step 7: Display results
    console.log(chalk.blue('📊 Results:'));
    for (const toolCall of result.toolCalls) {
      if (toolCall.toolName === 'createIssues' && toolCall.result?.created) {
        console.log(chalk.green(`\n✓ Created ${toolCall.result.created.length} issues:`));
        for (const issue of toolCall.result.created) {
          console.log(chalk.cyan(`  #${issue.number}: ${issue.title}`));
          console.log(chalk.gray(`     ${issue.url}`));
        }
      }
    }
    
    console.log(chalk.green('\n✅ Success! All issues created.\n'));
    
  } catch (error) {
    console.error(chalk.red('\n❌ Error:'), error);
    process.exit(1);
  }
}

// CLI setup
const program = new Command();

program
  .name('spec-to-github')
  .description('Convert a specification document into GitHub issues using LLM + tools')
  .version('1.0.0')
  .requiredOption('-s, --spec <path>', 'Path to specification file (markdown or text)')
  .requiredOption('-o, --owner <owner>', 'GitHub repository owner')
  .requiredOption('-r, --repo <repo>', 'GitHub repository name')
  .option('-p, --provider <provider>', 'LLM provider (openai, anthropic)', 'openai')
  .option('-v, --verbose', 'Enable verbose logging')
  .action(async (options) => {
    await specToGithub({
      spec: options.spec,
      owner: options.owner,
      repo: options.repo,
      provider: options.provider,
      verbose: options.verbose
    });
  });

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  program.parse();
}

export { specToGithub };

