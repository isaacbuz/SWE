/**
 * Credential Vault
 * 
 * Secure credential management for external API wrappers.
 * Credentials are never exposed to LLMs or logged.
 */

export interface CredentialConfig {
  /** API key or token */
  apiKey?: string;
  
  /** OAuth token */
  oauthToken?: string;
  
  /** Username for basic auth */
  username?: string;
  
  /** Password for basic auth */
  password?: string;
  
  /** Custom headers */
  headers?: Record<string, string>;
}

export class CredentialVault {
  private credentials: Map<string, CredentialConfig> = new Map();

  /**
   * Store credentials for an API
   */
  setCredentials(apiName: string, config: CredentialConfig): void {
    // Validate that credentials are provided
    if (!config.apiKey && !config.oauthToken && !config.username) {
      throw new Error(`No credentials provided for ${apiName}`);
    }

    // Store credentials (in production, use encrypted storage)
    this.credentials.set(apiName, { ...config });
  }

  /**
   * Get credentials for an API
   */
  getCredentials(apiName: string): CredentialConfig | undefined {
    return this.credentials.get(apiName);
  }

  /**
   * Get authorization header for an API
   */
  getAuthHeader(apiName: string): Record<string, string> | undefined {
    const creds = this.getCredentials(apiName);
    if (!creds) {
      return undefined;
    }

    const headers: Record<string, string> = {};

    if (creds.apiKey) {
      headers["Authorization"] = `Bearer ${creds.apiKey}`;
    } else if (creds.oauthToken) {
      headers["Authorization"] = `Bearer ${creds.oauthToken}`;
    } else if (creds.username && creds.password) {
      const basicAuth = Buffer.from(`${creds.username}:${creds.password}`).toString("base64");
      headers["Authorization"] = `Basic ${basicAuth}`;
    }

    // Add custom headers
    if (creds.headers) {
      Object.assign(headers, creds.headers);
    }

    return headers;
  }

  /**
   * Check if credentials exist for an API
   */
  hasCredentials(apiName: string): boolean {
    return this.credentials.has(apiName);
  }

  /**
   * Remove credentials for an API
   */
  removeCredentials(apiName: string): boolean {
    return this.credentials.delete(apiName);
  }

  /**
   * Clear all credentials
   */
  clear(): void {
    this.credentials.clear();
  }

  /**
   * List all configured APIs
   */
  listApis(): string[] {
    return Array.from(this.credentials.keys());
  }
}

