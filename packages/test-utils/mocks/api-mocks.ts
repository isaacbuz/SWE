export interface MockResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

export const createMockResponse = <T>(
  data: T,
  status: number = 200,
  statusText: string = "OK",
): MockResponse<T> => {
  return {
    data,
    status,
    statusText,
    headers: {
      "content-type": "application/json",
    },
  };
};

export const createMockErrorResponse = (
  message: string,
  status: number = 500,
): MockResponse => {
  return createMockResponse(
    {
      error: message,
      timestamp: new Date().toISOString(),
    },
    status,
    "Error",
  );
};

export class MockAPIClient {
  private handlers: Map<string, Function> = new Map();

  public on(endpoint: string, handler: Function) {
    this.handlers.set(endpoint, handler);
  }

  public async request(endpoint: string, options?: any) {
    const handler = this.handlers.get(endpoint);
    if (!handler) {
      return createMockErrorResponse("Not Found", 404);
    }
    return handler(options);
  }

  public reset() {
    this.handlers.clear();
  }
}
