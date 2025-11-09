/**
 * Credential management interface
 * 
 * Provides secure access to API credentials without exposing them to LLMs
 */

export interface CredentialVault {
  /**
   * Get credentials for a service
   * 
   * @param service - Service identifier (e.g., 'github', 'gsa')
   * @returns Credentials object (never expose to LLMs)
   */
  getCredentials(service: string): Promise<Credentials | null>;

  /**
   * Check if credentials exist for a service
   */
  hasCredentials(service: string): Promise<boolean>;
}

export interface Credentials {
  /**
   * API token or key
   */
  token?: string;

  /**
   * API key
   */
  apiKey?: string;

  /**
   * OAuth token
   */
  oauthToken?: string;

  /**
   * Additional service-specific credentials
   */
  [key: string]: unknown;
}

/**
 * Environment-based credential vault
 * Reads credentials from environment variables
 */
export class EnvironmentCredentialVault implements CredentialVault {
  async getCredentials(service: string): Promise<Credentials | null> {
    const token = process.env[`${service.toUpperCase()}_TOKEN`] ||
                  process.env[`${service.toUpperCase()}_API_KEY`];

    if (!token) {
      return null;
    }

    return { token };
  }

  async hasCredentials(service: string): Promise<boolean> {
    const creds = await this.getCredentials(service);
    return creds !== null;
  }
}

