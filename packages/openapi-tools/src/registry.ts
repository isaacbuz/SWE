/**
 * OpenAPI Tool Registry
 * 
 * Manages tool specifications loaded from OpenAPI specs and provides
 * unified access to all available tools.
 */
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { ToolSpec, ToolRegistryOptions } from './types';
import { OpenAPIV3, OpenAPIV3_1 } from 'openapi-types';

export class ToolRegistry {
  private tools: Map<string, ToolSpec> = new Map();
  private specPaths: string[] = [];

  constructor(options: ToolRegistryOptions = {}) {
    if (options.specPaths) {
      this.loadSpecs(options.specPaths, options.validateOnLoad ?? true);
    }
  }

  /**
   * Load OpenAPI specifications from file paths
   */
  async loadSpecs(
    paths: string[],
    validate: boolean = true
  ): Promise<void> {
    this.specPaths = paths;

    for (const path of paths) {
      try {
        const spec = this.loadSpecFile(path);
        
        if (validate) {
          this.validateSpec(spec);
        }

        const tools = this.extractTools(spec);
        this.registerTools(tools);
      } catch (error) {
        throw new Error(
          `Failed to load OpenAPI spec from ${path}: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  }

  /**
   * Get all tool specifications
   */
  getToolSpecs(): ToolSpec[] {
    return Array.from(this.tools.values());
  }

  /**
   * Get a tool specification by name
   */
  getToolByName(name: string): ToolSpec | undefined {
    return this.tools.get(name);
  }

  /**
   * Check if a tool exists
   */
  hasTool(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * Get tools by tag/category
   */
  getToolsByTag(tag: string): ToolSpec[] {
    return Array.from(this.tools.values()).filter(
      tool => tool.tags?.includes(tag)
    );
  }

  /**
   * Get all unique tags
   */
  getAllTags(): string[] {
    const tags = new Set<string>();
    for (const tool of this.tools.values()) {
      tool.tags?.forEach(tag => tags.add(tag));
    }
    return Array.from(tags);
  }

  /**
   * Get registry statistics
   */
  getStats() {
    return {
      totalTools: this.tools.size,
      tags: this.getAllTags().length,
      specPaths: this.specPaths.length,
    };
  }

  private loadSpecFile(path: string): OpenAPIV3.Document | OpenAPIV3_1.Document {
    const fullPath = resolve(path);
    const content = readFileSync(fullPath, 'utf-8');
    
    // Support both JSON and YAML
    if (path.endsWith('.json')) {
      return JSON.parse(content);
    } else {
      // For YAML, we'd need a YAML parser
      // For now, assume JSON format
      try {
        return JSON.parse(content);
      } catch {
        throw new Error('YAML parsing not yet implemented. Please use JSON format.');
      }
    }
  }

  private validateSpec(spec: OpenAPIV3.Document | OpenAPIV3_1.Document): void {
    if (!spec.openapi || (!spec.openapi.startsWith('3.0') && !spec.openapi.startsWith('3.1'))) {
      throw new Error('OpenAPI spec must be version 3.0 or 3.1');
    }

    if (!spec.paths || Object.keys(spec.paths).length === 0) {
      throw new Error('OpenAPI spec must contain at least one path');
    }
  }

  private extractTools(spec: OpenAPIV3.Document | OpenAPIV3_1.Document): ToolSpec[] {
    const tools: ToolSpec[] = [];

    if (!spec.paths) {
      return tools;
    }

    for (const [path, pathItem] of Object.entries(spec.paths)) {
      if (!pathItem) continue;

      const methods = ['get', 'post', 'put', 'patch', 'delete'] as const;
      
      for (const method of methods) {
        const operation = pathItem[method];
        if (!operation) continue;

        const operationId = operation.operationId;
        if (!operationId) {
          console.warn(`Skipping operation without operationId: ${method.toUpperCase()} ${path}`);
          continue;
        }

        // Extract request body schema
        let jsonSchema: Record<string, any> = {
          type: 'object',
          properties: {},
          required: [],
        };

        // Extract parameters
        if (operation.parameters) {
          for (const param of operation.parameters) {
            if ('schema' in param && param.schema) {
              const paramSchema = param.schema as OpenAPIV3.SchemaObject;
              jsonSchema.properties[param.name] = paramSchema;
              if (param.required) {
                jsonSchema.required.push(param.name);
              }
            }
          }
        }

        // Extract request body
        if (operation.requestBody && 'content' in operation.requestBody) {
          const content = operation.requestBody.content;
          const jsonContent = content['application/json'];
          if (jsonContent?.schema) {
            jsonSchema = jsonContent.schema as Record<string, any>;
          }
        }

        // Extract tags
        const tags = operation.tags || [];

        const tool: ToolSpec = {
          name: operationId,
          description: operation.description || operation.summary || '',
          jsonSchema,
          operationId,
          endpoint: path,
          method: method.toUpperCase(),
          tags,
          requiresAuth: operation.security !== undefined && operation.security.length > 0,
        };

        tools.push(tool);
      }
    }

    return tools;
  }

  private registerTools(tools: ToolSpec[]): void {
    for (const tool of tools) {
      if (this.tools.has(tool.name)) {
        console.warn(`Tool ${tool.name} already exists. Overwriting.`);
      }
      this.tools.set(tool.name, tool);
    }
  }
}

