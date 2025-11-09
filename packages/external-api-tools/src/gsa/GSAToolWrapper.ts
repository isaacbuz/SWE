/**
 * GSA (General Services Administration) API Tool Wrapper
 *
 * Wraps GSA/Data.gov APIs for government data access.
 * Handles authentication, rate limiting, caching, and retries.
 */

import { CredentialVault, CredentialConfig } from "../utils/CredentialVault.js";
import { ResponseCache } from "../utils/ResponseCache.js";
import { RetryHandler } from "../utils/RetryHandler.js";

export interface SearchSAMEntityArgs {
  query: string;
  limit?: number;
  filters?: {
    entity_type?: string;
    state?: string;
    naics_code?: string;
  };
}

export interface SearchSAMEntityResult {
  success: boolean;
  results: Array<{
    name: string;
    uei: string;
    entity_type: string;
    address?: string;
  }>;
  total: number;
}

export interface SearchContractOpportunitiesArgs {
  query?: string;
  posted_from?: string;
  posted_to?: string;
  limit?: number;
}

export interface SearchContractOpportunitiesResult {
  success: boolean;
  opportunities: Array<{
    title: string;
    opportunity_id: string;
    posted_date: string;
    closing_date: string;
    award_amount?: number;
  }>;
  total: number;
}

export class GSAToolWrapper {
  private baseUrl = "https://api.sam.gov";
  private credentialVault: CredentialVault;
  private cache: ResponseCache;
  private retryHandler: RetryHandler;

  constructor(
    credentialVault: CredentialVault,
    cache?: ResponseCache,
    retryHandler?: RetryHandler,
  ) {
    this.credentialVault = credentialVault;
    this.cache = cache || new ResponseCache(600000); // 10 min default (gov data changes slowly)
    this.retryHandler = retryHandler || new RetryHandler();
  }

  /**
   * Set GSA API credentials
   */
  setCredentials(config: CredentialConfig): void {
    this.credentialVault.setCredentials("gsa", config);
  }

  /**
   * Search SAM.gov entities
   */
  async searchSAMEntity(
    args: SearchSAMEntityArgs,
  ): Promise<SearchSAMEntityResult> {
    const authHeaders = this.credentialVault.getAuthHeader("gsa");
    const params = new URLSearchParams({
      q: args.query,
      limit: String(args.limit || 50),
    });

    if (args.filters) {
      if (args.filters.entity_type) {
        params.append("entityType", args.filters.entity_type);
      }
      if (args.filters.state) {
        params.append("state", args.filters.state);
      }
      if (args.filters.naics_code) {
        params.append("naicsCode", args.filters.naics_code);
      }
    }

    const cacheKey = `sam-entity-${params.toString()}`;
    let results = this.cache.get<SearchSAMEntityResult>(cacheKey);

    if (!results) {
      results = await this.retryHandler.execute(async () => {
        const response = await fetch(
          `${this.baseUrl}/entity-information/v3/entities?${params}`,
          {
            headers: {
              ...authHeaders,
              Accept: "application/json",
            },
          },
        );

        if (!response.ok) {
          throw new Error(`GSA API error: ${response.status}`);
        }

        const data = await response.json();
        return {
          success: true,
          results: (data.entityData || []).map((entity: any) => ({
            name: entity.entityRegistration?.legalBusinessName,
            uei: entity.entityRegistration?.ueiSAM,
            entity_type: entity.entityRegistration?.entityStructure,
            address: entity.entityRegistration?.physicalAddress?.addressLine1,
          })),
          total: data.totalRecords || 0,
        };
      });

      this.cache.set(cacheKey, results);
    }

    return results;
  }

  /**
   * Search contract opportunities
   */
  async searchContractOpportunities(
    args: SearchContractOpportunitiesArgs,
  ): Promise<SearchContractOpportunitiesResult> {
    const authHeaders = this.credentialVault.getAuthHeader("gsa");
    const params = new URLSearchParams();

    if (args.query) {
      params.append("q", args.query);
    }
    if (args.posted_from) {
      params.append("postedFrom", args.posted_from);
    }
    if (args.posted_to) {
      params.append("postedTo", args.posted_to);
    }
    params.append("limit", String(args.limit || 50));

    const cacheKey = `contract-opps-${params.toString()}`;
    let results = this.cache.get<SearchContractOpportunitiesResult>(cacheKey);

    if (!results) {
      results = await this.retryHandler.execute(async () => {
        const response = await fetch(
          `${this.baseUrl}/opportunities/v2/search?${params}`,
          {
            headers: {
              ...authHeaders,
              Accept: "application/json",
            },
          },
        );

        if (!response.ok) {
          throw new Error(`GSA API error: ${response.status}`);
        }

        const data = await response.json();
        return {
          success: true,
          opportunities: (data.opportunitiesData || []).map((opp: any) => ({
            title: opp.title,
            opportunity_id: opp.opportunityId,
            posted_date: opp.postedDate,
            closing_date: opp.closeDate,
            award_amount: opp.awardAmount,
          })),
          total: data.totalRecords || 0,
        };
      });

      this.cache.set(cacheKey, results);
    }

    return results;
  }
}
