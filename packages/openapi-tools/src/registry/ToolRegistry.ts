/**
 * OpenAPI Tool Registry
 * 
 * Manages tool specifications loaded from OpenAPI specifications.
 * Provides tool discovery, lookup, and management capabilities.
 */

import { ToolSpec, OpenAPISpec, ToolRegistryOptions } from "../types/index.js";
import { openApiToToolSpecs } from "../converter/index.js";

export class ToolRegistry {
  private tools: Map<string, ToolSpec> = new Map();
  private specs: OpenAPISpec[] = [];
  private options: Required<ToolRegistryOptions>;

  constructor(options: ToolRegistryOptions = {}) {
    this.options = {
      validate: options.validate ?? true,
      merge: options.merge ?? true,
      schemaConverter: options.schemaConverter ?? this.defaultSchemaConverter,
    };
  }

  /**
   * Load OpenAPI specification(s) and register tools
   * 
   * @param specs - OpenAPI specification objects or file paths
   */
  async loadSpecs(specs: (OpenAPISpec | string)[]): Promise<void> {
    const loadedSpecs: OpenAPISpec[] = [];

    for (const spec of specs) {
      let openApiSpec: OpenAPISpec;

      if (typeof spec === "string") {
        // Load from file path
        openApiSpec = await this.loadSpecFromFile(spec);
      } else {
        openApiSpec = spec;
      }

      // Validate if enabled
      if (this.options.validate) {
        this.validateSpec(openApiSpec);
      }

      loadedSpecs.push(openApiSpec);
    }

    // Merge specs if enabled
    if (this.options.merge && loadedSpecs.length > 1) {
      const merged = this.mergeSpecs(loadedSpecs);
      this.specs = [merged];
    } else {
      this.specs = loadedSpecs;
    }

    // Extract and register tools
    for (const spec of this.specs) {
      const toolSpecs = openApiToToolSpecs(spec, this.options.schemaConverter);
      this.registerTools(toolSpecs);
    }
  }

  /**
   * Get all registered tool specifications
   */
  getToolSpecs(): ToolSpec[] {
    return Array.from(this.tools.values());
  }

  /**
   * Get tool specification by name
   */
  getToolByName(name: string): ToolSpec | undefined {
    return this.tools.get(name);
  }

  /**
   * Get tools by category/tag
   */
  getToolsByCategory(category: string): ToolSpec[] {
    return Array.from(this.tools.values()).filter(
      (tool) => tool.category === category
    );
  }

  /**
   * Check if tool exists
   */
  hasTool(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * Get number of registered tools
   */
  getToolCount(): number {
    return this.tools.size;
  }

  /**
   * Clear all registered tools
   */
  clear(): void {
    this.tools.clear();
    this.specs = [];
  }

  /**
   * Register multiple tools
   */
  private registerTools(toolSpecs: ToolSpec[]): void {
    for (const toolSpec of toolSpecs) {
      if (this.tools.has(toolSpec.name)) {
        console.warn(`Tool '${toolSpec.name}' already exists, overwriting`);
      }
      this.tools.set(toolSpec.name, toolSpec);
    }
  }

  /**
   * Load OpenAPI spec from file
   */
  private async loadSpecFromFile(path: string): Promise<OpenAPISpec> {
    // In Node.js environment, use fs/promises
    if (typeof window === "undefined") {
      const fs = await import("fs/promises");
      const content = await fs.readFile(path, "utf-8");
      
      // Try JSON first, then YAML
      try {
        return JSON.parse(content) as OpenAPISpec;
      } catch {
        const yaml = await import("yaml");
        return yaml.parse(content) as OpenAPISpec;
      }
    }
    
    throw new Error("File loading not supported in browser environment");
  }

  /**
   * Validate OpenAPI specification
   */
  private validateSpec(spec: OpenAPISpec): void {
    if (!spec.openapi) {
      throw new Error("Invalid OpenAPI spec: missing 'openapi' field");
    }

    const version = parseFloat(spec.openapi);
    if (version < 3.0 || version >= 4.0) {
      throw new Error(
        `Unsupported OpenAPI version: ${spec.openapi}. Supported: 3.0.x - 3.1.x`
      );
    }

    if (!spec.info || !spec.info.title || !spec.info.version) {
      throw new Error("Invalid OpenAPI spec: missing required 'info' fields");
    }

    if (!spec.paths || Object.keys(spec.paths).length === 0) {
      console.warn("OpenAPI spec has no paths defined");
    }
  }

  /**
   * Merge multiple OpenAPI specs into one
   */
  private mergeSpecs(specs: OpenAPISpec[]): OpenAPISpec {
    if (specs.length === 0) {
      throw new Error("Cannot merge empty spec list");
    }

    if (specs.length === 1) {
      return specs[0];
    }

    const merged: OpenAPISpec = {
      openapi: specs[0].openapi,
      info: {
        title: "Merged API",
        version: "1.0.0",
        description: `Merged from ${specs.length} specifications`,
      },
      paths: {},
      components: {
        schemas: {},
        parameters: {},
      },
    };

    // Merge paths
    for (const spec of specs) {
      if (spec.paths) {
        Object.assign(merged.paths, spec.paths);
      }

      // Merge components
      if (spec.components) {
        if (spec.components.schemas) {
          Object.assign(merged.components!.schemas!, spec.components.schemas);
        }
        if (spec.components.parameters) {
          Object.assign(
            merged.components!.parameters!,
            spec.components.parameters
          );
        }
      }
    }

    return merged;
  }

  /**
   * Default schema converter (identity function)
   */
  private defaultSchemaConverter(schema: unknown): Record<string, unknown> {
    if (typeof schema === "object" && schema !== null) {
      return schema as Record<string, unknown>;
    }
    return {};
  }
}

