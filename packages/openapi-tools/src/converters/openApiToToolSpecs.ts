import { OpenAPIV3, OpenAPIV3_1 } from 'openapi-types';
import { ToolSpec } from '../types/ToolSpec';

type OpenAPIDocument = OpenAPIV3.Document | OpenAPIV3_1.Document;
type OpenAPIPathItem = OpenAPIV3.PathItemObject | OpenAPIV3_1.PathItemObject;
type OpenAPIOperation = OpenAPIV3.OperationObject | OpenAPIV3_1.OperationObject;

/**
 * Convert OpenAPI specification to ToolSpec array
 * 
 * Extracts all operations from OpenAPI paths and converts them to
 * tool specifications that can be used by LLM providers.
 * 
 * @param api - OpenAPI document (3.0 or 3.1)
 * @param operationIdResolver - Function to generate operationId if missing
 * @returns Array of ToolSpec objects
 */
export function openApiToToolSpecs(
  api: OpenAPIDocument,
  operationIdResolver?: (method: string, path: string) => string
): ToolSpec[] {
  const tools: ToolSpec[] = [];
  const paths = api.paths || {};

  for (const [path, pathItem] of Object.entries(paths)) {
    if (!pathItem) continue;

    const methods: Array<keyof OpenAPIPathItem> = [
      'get',
      'post',
      'put',
      'patch',
      'delete',
      'options',
      'head',
    ];

    for (const method of methods) {
      const operation = pathItem[method] as OpenAPIOperation | undefined;
      if (!operation) continue;

      // Skip if operation is not an object (shouldn't happen but type-safe)
      if (typeof operation !== 'object') continue;

      // Get or generate operationId
      let operationId = operation.operationId;
      if (!operationId) {
        if (operationIdResolver) {
          operationId = operationIdResolver(method.toUpperCase(), path);
        } else {
          // Skip operations without operationId if no resolver provided
          continue;
        }
      }

      // Extract description
      const description =
        operation.description ||
        operation.summary ||
        `${method.toUpperCase()} ${path}`;

      // Extract JSON Schema from requestBody or parameters
      const jsonSchema = extractJsonSchema(operation, method.toUpperCase());

      // Extract tags
      const tags = operation.tags || [];

      // Build ToolSpec
      const toolSpec: ToolSpec = {
        name: operationId,
        description: description,
        jsonSchema: jsonSchema,
        operationId: operationId,
        endpoint: path,
        method: method.toUpperCase(),
        tags: tags,
        metadata: {
          summary: operation.summary,
          deprecated: operation.deprecated || false,
        },
      };

      tools.push(toolSpec);
    }
  }

  return tools;
}

/**
 * Extract JSON Schema from OpenAPI operation
 * 
 * Prioritizes requestBody schema, falls back to parameters schema
 */
function extractJsonSchema(
  operation: OpenAPIOperation,
  method: string
): object {
  // Try to get schema from requestBody (for POST, PUT, PATCH)
  if (['POST', 'PUT', 'PATCH'].includes(method)) {
    const requestBody = operation.requestBody;
    if (requestBody && '$ref' in requestBody) {
      // Handle $ref - would need to resolve, for now return empty schema
      return { type: 'object', properties: {} };
    }

    if (requestBody && 'content' in requestBody) {
      const content = requestBody.content;
      const jsonContent = content['application/json'];
      
      if (jsonContent?.schema) {
        return convertOpenAPISchemaToJSONSchema(jsonContent.schema);
      }
    }
  }

  // Fall back to parameters schema
  const parameters = operation.parameters || [];
  if (parameters.length > 0) {
    return parametersToJsonSchema(parameters);
  }

  // Default empty schema
  return { type: 'object', properties: {} };
}

/**
 * Convert OpenAPI schema to JSON Schema
 */
function convertOpenAPISchemaToJSONSchema(
  schema: OpenAPIV3.SchemaObject | OpenAPIV3_1.SchemaObject | OpenAPIV3.ReferenceObject | OpenAPIV3_1.ReferenceObject
): object {
  // Handle $ref
  if ('$ref' in schema) {
    // Would need to resolve reference - for now return empty
    return { type: 'object', properties: {} };
  }

  // OpenAPI 3.0/3.1 schemas are mostly JSON Schema compatible
  // Just return as-is (may need adjustments for specific cases)
  return schema as object;
}

/**
 * Convert OpenAPI parameters to JSON Schema
 */
function parametersToJsonSchema(
  parameters: Array<OpenAPIV3.ParameterObject | OpenAPIV3_1.ParameterObject | OpenAPIV3.ReferenceObject | OpenAPIV3_1.ReferenceObject>
): object {
  const properties: Record<string, unknown> = {};
  const required: string[] = [];

  for (const param of parameters) {
    // Handle $ref
    if ('$ref' in param) {
      continue; // Would need to resolve reference
    }

    const paramObj = param as OpenAPIV3.ParameterObject | OpenAPIV3_1.ParameterObject;
    
    // Only include query, header, path, cookie parameters
    // Body parameters should come from requestBody
    if (!['query', 'header', 'path', 'cookie'].includes(paramObj.in)) {
      continue;
    }

    const name = paramObj.name;
    const schema = paramObj.schema || { type: 'string' };

    properties[name] = convertOpenAPISchemaToJSONSchema(schema);

    if (paramObj.required) {
      required.push(name);
    }
  }

  return {
    type: 'object',
    properties,
    ...(required.length > 0 ? { required } : {}),
  };
}

