import SwaggerParser from 'swagger-parser';
import { OpenAPIV3, OpenAPIV3_1 } from 'openapi-types';
import { ToolSpec, ToolRegistryOptions, LoadedSpec } from '../types/ToolSpec';
import { openApiToToolSpecs } from '../converters/openApiToToolSpecs';

/**
 * ToolRegistry - Manages OpenAPI tool specifications
 * 
 * Loads and maintains a unified registry of tools from multiple OpenAPI specs.
 * Provides methods to query and retrieve tool specifications for LLM providers.
 */
export class ToolRegistry {
  private tools: Map<string, ToolSpec> = new Map();
  private loadedSpecs: LoadedSpec[] = [];
  private options: Required<ToolRegistryOptions>;

  constructor(options: ToolRegistryOptions = {}) {
    this.options = {
      validateOnLoad: options.validateOnLoad ?? true,
      allowDuplicates: options.allowDuplicates ?? false,
      operationIdResolver: options.operationIdResolver ?? this.defaultOperationIdResolver,
    };
  }

  /**
   * Load one or more OpenAPI specification files
   * 
   * @param paths - Array of file paths or URLs to OpenAPI specs
   * @throws Error if spec is invalid or duplicate operationIds found
   */
  async loadSpecs(paths: string[]): Promise<void> {
    for (const path of paths) {
      await this.loadSpec(path);
    }
  }

  /**
   * Load a single OpenAPI specification file
   * 
   * @param path - File path or URL to OpenAPI spec
   */
  private async loadSpec(path: string): Promise<void> {
    try {
      // Parse and validate OpenAPI spec
      let api: OpenAPIV3.Document | OpenAPIV3_1.Document;
      
      if (this.options.validateOnLoad) {
        api = (await SwaggerParser.validate(path)) as OpenAPIV3.Document | OpenAPIV3_1.Document;
      } else {
        api = (await SwaggerParser.parse(path)) as OpenAPIV3.Document | OpenAPIV3_1.Document;
      }

      // Extract tools from OpenAPI spec
      const toolSpecs = openApiToToolSpecs(api, this.options.operationIdResolver);

      // Check for duplicates
      const duplicates: string[] = [];
      for (const tool of toolSpecs) {
        if (this.tools.has(tool.name) && !this.options.allowDuplicates) {
          duplicates.push(tool.name);
        }
      }

      if (duplicates.length > 0) {
        throw new Error(
          `Duplicate operationIds found: ${duplicates.join(', ')}. ` +
          `Set allowDuplicates=true to override.`
        );
      }

      // Add tools to registry
      for (const tool of toolSpecs) {
        this.tools.set(tool.name, tool);
      }

      // Record loaded spec metadata
      const loadedSpec: LoadedSpec = {
        path,
        version: api.openapi,
        title: api.info?.title,
        toolCount: toolSpecs.length,
        loadedAt: new Date(),
      };

      this.loadedSpecs.push(loadedSpec);
    } catch (error) {
      throw new Error(`Failed to load OpenAPI spec from ${path}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Get all tool specifications
   * 
   * @returns Array of all registered tools
   */
  getToolSpecs(): ToolSpec[] {
    return Array.from(this.tools.values());
  }

  /**
   * Get a tool by name (operationId)
   * 
   * @param name - Tool name (operationId)
   * @returns ToolSpec or undefined if not found
   */
  getToolByName(name: string): ToolSpec | undefined {
    return this.tools.get(name);
  }

  /**
   * Get tools by tag
   * 
   * @param tag - Tag to filter by
   * @returns Array of tools with the specified tag
   */
  getToolsByTag(tag: string): ToolSpec[] {
    return Array.from(this.tools.values()).filter(
      (tool) => tool.tags?.includes(tag)
    );
  }

  /**
   * Get tools by endpoint prefix
   * 
   * @param prefix - Endpoint path prefix
   * @returns Array of tools matching the prefix
   */
  getToolsByEndpointPrefix(prefix: string): ToolSpec[] {
    return Array.from(this.tools.values()).filter(
      (tool) => tool.endpoint?.startsWith(prefix)
    );
  }

  /**
   * Check if a tool exists
   * 
   * @param name - Tool name (operationId)
   * @returns True if tool exists
   */
  hasTool(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * Get count of registered tools
   * 
   * @returns Number of tools in registry
   */
  getToolCount(): number {
    return this.tools.size;
  }

  /**
   * Get metadata about loaded specs
   * 
   * @returns Array of loaded spec metadata
   */
  getLoadedSpecs(): ReadonlyArray<LoadedSpec> {
    return [...this.loadedSpecs];
  }

  /**
   * Clear all tools and loaded specs
   */
  clear(): void {
    this.tools.clear();
    this.loadedSpecs = [];
  }

  /**
   * Remove a specific tool
   * 
   * @param name - Tool name (operationId) to remove
   * @returns True if tool was removed, false if not found
   */
  removeTool(name: string): boolean {
    return this.tools.delete(name);
  }

  /**
   * Default operationId resolver
   * Generates operationId from method and path if missing
   */
  private defaultOperationIdResolver(method: string, path: string): string {
    // Convert path to camelCase
    const pathParts = path
      .split('/')
      .filter((p) => p && !p.startsWith('{'))
      .map((p) => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase());
    
    const methodLower = method.toLowerCase();
    const operationId = methodLower + pathParts.join('');
    
    return operationId.charAt(0).toLowerCase() + operationId.slice(1);
  }
}

