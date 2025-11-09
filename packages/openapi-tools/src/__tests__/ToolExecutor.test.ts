import { describe, expect, it } from "vitest";

import { ToolExecutor } from "../executor/ToolExecutor.js";
import { CircuitBreaker } from "../executor/CircuitBreaker.js";

const baseOptions = {
  validate: false,
  rateLimit: false,
  checkPermissions: false,
};

describe("ToolExecutor - circuit breaker integration", () => {
  it("prevents execution when circuit is open", async () => {
    const breaker = new CircuitBreaker({ failureThreshold: 1, resetTimeoutMs: 60_000 });
    const executor = new ToolExecutor({
      ...baseOptions,
      circuitBreaker: true,
      circuitBreakerInstance: breaker,
    });

    executor.registerTool("unstable", () => {
      throw new Error("boom");
    });

    await executor.execute("unstable", {});

    const result = await executor.execute("unstable", {});

    expect(result.success).toBe(false);
    expect(result.error).toContain("Circuit breaker is open");
  });

  it("allows execution when circuit breaker is closed", async () => {
    const breaker = new CircuitBreaker({ failureThreshold: 3 });
    const executor = new ToolExecutor({
      ...baseOptions,
      circuitBreaker: true,
      circuitBreakerInstance: breaker,
    });

    executor.registerTool("stable", () => "ok");

    const result = await executor.execute("stable", {});

    expect(result.success).toBe(true);
    expect(result.result).toBe("ok");
  });
});
