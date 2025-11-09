export class MockWebSocket {
  public readyState: number = WebSocket.CONNECTING;
  public url: string;
  private listeners: Map<string, Set<Function>> = new Map();

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.trigger("open", {});
    }, 0);
  }

  public send(data: string | ArrayBufferLike | Blob | ArrayBufferView) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not open");
    }
    // Echo back for testing
    setTimeout(() => {
      this.trigger("message", { data });
    }, 0);
  }

  public close(code?: number, reason?: string) {
    this.readyState = WebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = WebSocket.CLOSED;
      this.trigger("close", { code, reason });
    }, 0);
  }

  public addEventListener(event: string, handler: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);
  }

  public removeEventListener(event: string, handler: Function) {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  private trigger(event: string, data: any) {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  // Helper methods for testing
  public simulateMessage(data: any) {
    this.trigger("message", { data: JSON.stringify(data) });
  }

  public simulateError(error: Error) {
    this.trigger("error", error);
  }

  public simulateClose(code: number = 1000, reason: string = "Normal closure") {
    this.close(code, reason);
  }
}

export const createMockWebSocket = (url: string = "ws://localhost:8000") => {
  return new MockWebSocket(url);
};
