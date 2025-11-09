/**
 * Tests for ToolRegistry
 */

import { describe, it, expect, beforeEach } from "vitest";
import { ToolRegistry } from "../registry/ToolRegistry.js";
import type { OpenAPISpec } from "../types/index.js";

describe("ToolRegistry", () => {
  let registry: ToolRegistry;

  beforeEach(() => {
    registry = new ToolRegistry();
  });

  describe("loadSpecs", () => {
    it("should load and register tools from OpenAPI spec", async () => {
      const spec: OpenAPISpec = {
        openapi: "3.1.0",
        info: {
          title: "Test API",
          version: "1.0.0",
        },
        paths: {
          "/users": {
            get: {
              operationId: "listUsers",
              summary: "List users",
              parameters: [
                {
                  name: "limit",
                  in: "query",
                  schema: { type: "integer" },
                },
              ],
            },
          },
        },
      };

      await registry.loadSpecs([spec]);

      expect(registry.getToolCount()).toBe(1);
      expect(registry.hasTool("listUsers")).toBe(true);

      const tool = registry.getToolByName("listUsers");
      expect(tool).toBeDefined();
      expect(tool?.name).toBe("listUsers");
      expect(tool?.description).toBe("List users");
    });

    it("should merge multiple specs when merge option is enabled", async () => {
      const spec1: OpenAPISpec = {
        openapi: "3.1.0",
        info: { title: "API 1", version: "1.0.0" },
        paths: {
          "/users": {
            get: {
              operationId: "listUsers",
              summary: "List users",
            },
          },
        },
      };

      const spec2: OpenAPISpec = {
        openapi: "3.1.0",
        info: { title: "API 2", version: "1.0.0" },
        paths: {
          "/posts": {
            get: {
              operationId: "listPosts",
              summary: "List posts",
            },
          },
        },
      };

      await registry.loadSpecs([spec1, spec2]);

      expect(registry.getToolCount()).toBe(2);
      expect(registry.hasTool("listUsers")).toBe(true);
      expect(registry.hasTool("listPosts")).toBe(true);
    });

    it("should skip operations without operationId", async () => {
      const spec: OpenAPISpec = {
        openapi: "3.1.0",
        info: { title: "Test API", version: "1.0.0" },
        paths: {
          "/users": {
            get: {
              summary: "List users",
              // Missing operationId
            },
          },
        },
      };

      await registry.loadSpecs([spec]);

      expect(registry.getToolCount()).toBe(0);
    });
  });

  describe("getToolByName", () => {
    it("should return tool if exists", async () => {
      const spec: OpenAPISpec = {
        openapi: "3.1.0",
        info: { title: "Test API", version: "1.0.0" },
        paths: {
          "/users": {
            get: {
              operationId: "listUsers",
              summary: "List users",
            },
          },
        },
      };

      await registry.loadSpecs([spec]);

      const tool = registry.getToolByName("listUsers");
      expect(tool).toBeDefined();
      expect(tool?.name).toBe("listUsers");
    });

    it("should return undefined if tool does not exist", () => {
      const tool = registry.getToolByName("nonexistent");
      expect(tool).toBeUndefined();
    });
  });

  describe("getToolsByCategory", () => {
    it("should return tools by category", async () => {
      const spec: OpenAPISpec = {
        openapi: "3.1.0",
        info: { title: "Test API", version: "1.0.0" },
        paths: {
          "/users": {
            get: {
              operationId: "listUsers",
              summary: "List users",
              tags: ["users"],
            },
          },
          "/posts": {
            get: {
              operationId: "listPosts",
              summary: "List posts",
              tags: ["posts"],
            },
          },
        },
      };

      await registry.loadSpecs([spec]);

      const userTools = registry.getToolsByCategory("users");
      expect(userTools.length).toBe(1);
      expect(userTools[0].name).toBe("listUsers");
    });
  });

  describe("clear", () => {
    it("should clear all registered tools", async () => {
      const spec: OpenAPISpec = {
        openapi: "3.1.0",
        info: { title: "Test API", version: "1.0.0" },
        paths: {
          "/users": {
            get: {
              operationId: "listUsers",
              summary: "List users",
            },
          },
        },
      };

      await registry.loadSpecs([spec]);
      expect(registry.getToolCount()).toBe(1);

      registry.clear();
      expect(registry.getToolCount()).toBe(0);
    });
  });
});

