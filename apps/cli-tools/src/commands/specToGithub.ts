#!/usr/bin/env node
/**
 * Spec to GitHub Issues Pipeline
 *
 * Takes a specification document and uses LLM + tools to create structured GitHub issues.
 */

import { readFile } from "fs/promises";
import { resolve } from "path";
import { Command } from "commander";
import chalk from "chalk";
import { ToolRegistry } from "@ai-company/openapi-tools";
import { ToolExecutor } from "@ai-company/openapi-tools";
import { ToolCallingPipeline } from "@ai-company/tool-pipeline";
import {
  GitHubToolWrapper,
  CredentialVault,
} from "@ai-company/external-api-tools";

interface SpecToGithubOptions {
  spec: string;
  owner: string;
  repo: string;
  provider?: string;
  model?: string;
  verbose?: boolean;
  dryRun?: boolean;
}

/**
 * Simple LLM Provider wrapper for OpenAI/Anthropic
 * In production, this would use the actual provider implementations
 */
class SimpleLLMProvider {
  name: string;
  private apiKey: string;
  private baseUrl: string;

  constructor(provider: string, apiKey: string) {
    this.name = provider;
    this.apiKey = apiKey;

    if (provider === "openai") {
      this.baseUrl = "https://api.openai.com/v1";
    } else if (provider === "anthropic") {
      this.baseUrl = "https://api.anthropic.com/v1";
    } else {
      throw new Error(`Unsupported provider: ${provider}`);
    }
  }

  async complete(
    messages: Array<{ role: string; content: string }>,
    tools: any[],
    systemPrompt?: string,
  ): Promise<{
    content: string;
    toolCalls?: Array<{
      name: string;
      arguments: any;
      id: string;
    }>;
  }> {
    // In production, this would call the actual LLM API
    // For now, we'll simulate a response that calls createIssues

    const lastMessage = messages[messages.length - 1];

    // Simulate LLM analyzing the spec and creating issues
    if (
      lastMessage.content.includes("specification") ||
      lastMessage.content.includes("spec")
    ) {
      // Parse the spec to extract tasks (simplified)
      const specContent = lastMessage.content;

      // Extract task titles (simplified parsing)
      const taskMatches = specContent.match(/##?\s+(.+)/g) || [];
      const tasks = taskMatches.slice(0, 5).map((match, index) => ({
        title: match.replace(/##?\s+/, "").trim(),
        body: `Task ${index + 1}: ${match.replace(/##?\s+/, "").trim()}\n\nThis task was automatically generated from the specification.`,
        labels: ["enhancement", "auto-generated"],
      }));

      return {
        content: `I've analyzed the specification and identified ${tasks.length} tasks. Creating GitHub issues now...`,
        toolCalls: [
          {
            name: "createIssues",
            arguments: {
              owner: this.extractOwner(messages),
              repo: this.extractRepo(messages),
              tasks: tasks,
            },
            id: `call_${Date.now()}`,
          },
        ],
      };
    }

    return {
      content: "I understand. Let me create the GitHub issues for you.",
    };
  }

  private extractOwner(messages: any[]): string {
    for (const msg of messages) {
      const match = msg.content.match(/owner[:\s]+(\w+)/i);
      if (match) return match[1];
    }
    return "isaacbuz";
  }

  private extractRepo(messages: any[]): string {
    for (const msg of messages) {
      const match = msg.content.match(/repo[:\s]+(\w+)/i);
      if (match) return match[1];
    }
    return "SWE";
  }
}

/**
 * Main function to convert spec to GitHub issues
 */
async function specToGithub(options: SpecToGithubOptions): Promise<void> {
  console.log(chalk.blue("🤖 Spec to GitHub Issues Pipeline\n"));

  try {
    // 1. Load spec file
    console.log(chalk.gray(`📄 Loading specification from: ${options.spec}`));
    const specPath = resolve(process.cwd(), options.spec);
    const spec = await readFile(specPath, "utf-8");
    console.log(
      chalk.green(`✅ Loaded specification (${spec.length} characters)`),
    );

    // 2. Initialize tool registry
    console.log(chalk.gray("🔧 Initializing tool registry..."));
    const toolRegistry = new ToolRegistry();
    await toolRegistry.loadSpecs(["./tools/openapi/ai-dev-tools.yaml"]);
    console.log(
      chalk.green(`✅ Loaded ${toolRegistry.getToolSpecs().length} tools`),
    );

    // 3. Initialize tool executor
    console.log(chalk.gray("⚙️  Setting up tool executor..."));
    const toolExecutor = new ToolExecutor({ checkPermissions: false });

    // Register GitHub tool handler
    const credentialVault = new CredentialVault();
    const githubWrapper = new GitHubToolWrapper(credentialVault);

    // Set GitHub credentials from environment
    const githubToken = process.env.GITHUB_TOKEN;
    if (githubToken) {
      credentialVault.setCredentials("github", {
        apiKey: githubToken,
      });
    }

    toolExecutor.registerTool("createIssues", async (args: any) => {
      if (options.dryRun) {
        console.log(
          chalk.yellow(`[DRY RUN] Would create ${args.tasks.length} issues`),
        );
        return {
          success: true,
          created: args.tasks.length,
          issues: args.tasks.map((task: any, i: number) => ({
            number: 1000 + i,
            url: `https://github.com/${args.owner}/${args.repo}/issues/${1000 + i}`,
            title: task.title,
          })),
        };
      }

      const result = await githubWrapper.createIssues({
        owner: args.owner,
        repo: args.repo,
        tasks: args.tasks,
      });

      return result;
    });

    console.log(chalk.green("✅ Tool executor ready"));

    // 4. Initialize LLM provider
    const provider = options.provider || "openai";
    const apiKey =
      provider === "openai"
        ? process.env.OPENAI_API_KEY
        : process.env.ANTHROPIC_API_KEY;

    if (!apiKey) {
      throw new Error(
        `API key not found. Please set ${provider === "openai" ? "OPENAI_API_KEY" : "ANTHROPIC_API_KEY"} environment variable.`,
      );
    }

    console.log(chalk.gray(`🤖 Initializing ${provider} provider...`));
    const llmProvider = new SimpleLLMProvider(provider, apiKey);
    console.log(chalk.green(`✅ Provider ready: ${llmProvider.name}`));

    // 5. Create pipeline
    console.log(chalk.gray("🔗 Creating tool calling pipeline..."));
    const pipeline = new ToolCallingPipeline(
      toolRegistry,
      toolExecutor,
      llmProvider,
      {
        maxTurns: 5,
        timeoutPerTurn: 30000,
      },
    );
    console.log(chalk.green("✅ Pipeline ready"));

    // 6. Execute with tools
    console.log(
      chalk.blue("\n📋 Analyzing specification and creating issues...\n"),
    );

    const prompt = `
You are a technical project planner. Analyze the following specification 
and break it down into well-structured GitHub issues.

Repository: ${options.owner}/${options.repo}

Specification:
${spec}

Use the createIssues tool to create the issues. Each issue should have:
- Clear, concise title
- Detailed description with acceptance criteria
- Appropriate labels (e.g., "enhancement", "feature", "bug")
- Dependencies noted if applicable

Break down the specification into logical, actionable tasks.
`;

    const result = await pipeline.execute(
      prompt,
      "You are a helpful technical assistant.",
    );

    // 7. Display results
    console.log(chalk.green("\n✅ Pipeline execution complete!\n"));
    console.log(chalk.bold("Results:"));
    console.log(`  Final Response: ${result.finalResponse}`);
    console.log(`  Tool Executions: ${result.toolResults.length}`);
    console.log(`  Total Turns: ${result.turns}`);
    console.log(`  Execution Time: ${result.totalExecutionTimeMs}ms\n`);

    // Extract issue numbers from tool results
    const issueNumbers: number[] = [];
    for (const toolResult of result.toolResults) {
      if (toolResult.name === "createIssues" && toolResult.success) {
        const resultData = toolResult.result as any;
        if (resultData.issues) {
          for (const issue of resultData.issues) {
            issueNumbers.push(issue.number);
            console.log(
              chalk.green(`  ✓ Created issue #${issue.number}: ${issue.title}`),
            );
            console.log(chalk.gray(`    ${issue.url}`));
          }
        }
      }
    }

    if (issueNumbers.length > 0) {
      console.log(
        chalk.green(
          `\n✅ Successfully created ${issueNumbers.length} issues: #${issueNumbers.join(", #")}`,
        ),
      );
    } else {
      console.log(
        chalk.yellow(
          "\n⚠️  No issues were created. Check the tool results above.",
        ),
      );
    }
  } catch (error: any) {
    console.error(chalk.red("\n❌ Error:"), error.message);
    if (options.verbose) {
      console.error(error);
    }
    process.exit(1);
  }
}

// CLI setup
const program = new Command();

program
  .name("spec-to-github")
  .description("Convert a specification document to GitHub issues using AI")
  .version("1.0.0")
  .requiredOption("-s, --spec <path>", "Path to specification file")
  .requiredOption("-o, --owner <owner>", "GitHub repository owner")
  .requiredOption("-r, --repo <repo>", "GitHub repository name")
  .option(
    "-p, --provider <provider>",
    "LLM provider (openai|anthropic)",
    "openai",
  )
  .option("-m, --model <model>", "Model name", "gpt-4")
  .option("-v, --verbose", "Verbose output")
  .option("--dry-run", "Dry run (don't actually create issues)")
  .action(specToGithub);

program.parse(process.argv);
