/**
 * Schema Validator
 *
 * Validates data against JSON Schema using Zod.
 */

import { z } from "zod";

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export class SchemaValidator {
  private schemas: Map<string, z.ZodSchema> = new Map();

  /**
   * Register a JSON Schema for a tool
   */
  registerSchema(name: string, jsonSchema: Record<string, unknown>): void {
    try {
      const zodSchema = this.jsonSchemaToZod(jsonSchema);
      this.schemas.set(name, zodSchema);
    } catch (error) {
      throw new Error(
        `Failed to register schema for '${name}': ${error instanceof Error ? error.message : String(error)}`,
      );
    }
  }

  /**
   * Unregister a schema
   */
  unregisterSchema(name: string): void {
    this.schemas.delete(name);
  }

  /**
   * Validate data against schema
   */
  validate(
    toolName: string,
    data: unknown,
    jsonSchema?: Record<string, unknown>,
  ): ValidationResult {
    // Use provided schema or registered schema
    let schema: z.ZodSchema | null = null;

    if (jsonSchema) {
      try {
        schema = this.jsonSchemaToZod(jsonSchema);
      } catch (error) {
        return {
          valid: false,
          errors: [
            `Schema conversion failed: ${error instanceof Error ? error.message : String(error)}`,
          ],
        };
      }
    } else {
      schema = this.schemas.get(toolName) || null;
    }

    if (!schema) {
      return {
        valid: false,
        errors: [`No schema registered for tool '${toolName}'`],
      };
    }

    try {
      schema.parse(data);
      return { valid: true, errors: [] };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return {
          valid: false,
          errors: error.errors.map((e) => `${e.path.join(".")}: ${e.message}`),
        };
      }
      return {
        valid: false,
        errors: [error instanceof Error ? error.message : String(error)],
      };
    }
  }

  /**
   * Convert JSON Schema to Zod schema
   */
  private jsonSchemaToZod(jsonSchema: Record<string, unknown>): z.ZodSchema {
    const type = jsonSchema.type as string | undefined;

    switch (type) {
      case "string":
        return this.stringSchema(jsonSchema);
      case "number":
      case "integer":
        return this.numberSchema(jsonSchema);
      case "boolean":
        return z.boolean();
      case "array":
        return this.arraySchema(jsonSchema);
      case "object":
        return this.objectSchema(jsonSchema);
      default:
        // Default to unknown if type not specified
        return z.unknown();
    }
  }

  /**
   * Create Zod string schema
   */
  private stringSchema(jsonSchema: Record<string, unknown>): z.ZodString {
    let schema = z.string();

    if (jsonSchema.minLength !== undefined) {
      schema = schema.min(jsonSchema.minLength as number);
    }
    if (jsonSchema.maxLength !== undefined) {
      schema = schema.max(jsonSchema.maxLength as number);
    }
    if (jsonSchema.pattern) {
      schema = schema.regex(new RegExp(jsonSchema.pattern as string));
    }
    if (jsonSchema.enum) {
      return z.enum(jsonSchema.enum as [string, ...string[]]);
    }

    return schema;
  }

  /**
   * Create Zod number schema
   */
  private numberSchema(jsonSchema: Record<string, unknown>): z.ZodNumber {
    let schema = jsonSchema.type === "integer" ? z.number().int() : z.number();

    if (jsonSchema.minimum !== undefined) {
      schema = schema.min(jsonSchema.minimum as number);
    }
    if (jsonSchema.maximum !== undefined) {
      schema = schema.max(jsonSchema.maximum as number);
    }

    return schema;
  }

  /**
   * Create Zod array schema
   */
  private arraySchema(
    jsonSchema: Record<string, unknown>,
  ): z.ZodArray<z.ZodTypeAny> {
    const items = jsonSchema.items as Record<string, unknown> | undefined;
    const itemSchema = items ? this.jsonSchemaToZod(items) : z.unknown();

    let schema = z.array(itemSchema);

    if (jsonSchema.minItems !== undefined) {
      schema = schema.min(jsonSchema.minItems as number);
    }
    if (jsonSchema.maxItems !== undefined) {
      schema = schema.max(jsonSchema.maxItems as number);
    }

    return schema;
  }

  /**
   * Create Zod object schema
   */
  private objectSchema(
    jsonSchema: Record<string, unknown>,
  ): z.ZodObject<Record<string, z.ZodTypeAny>> {
    const properties = (jsonSchema.properties as Record<string, unknown>) || {};
    const required = (jsonSchema.required as string[]) || [];

    const shape: Record<string, z.ZodTypeAny> = {};

    for (const [key, propSchema] of Object.entries(properties)) {
      const zodProp = this.jsonSchemaToZod(
        propSchema as Record<string, unknown>,
      );
      shape[key] = required.includes(key) ? zodProp : zodProp.optional();
    }

    return z.object(shape);
  }
}
