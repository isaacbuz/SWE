/**
 * External API Tools Package
 *
 * Provides wrappers for external APIs (GitHub, GSA, etc.)
 * with credential management, rate limiting, caching, and retries.
 */

export { GitHubToolWrapper } from "./github/GitHubToolWrapper.js";
export { GSAToolWrapper } from "./gsa/GSAToolWrapper.js";
export { CredentialVault } from "./utils/CredentialVault.js";
export { ResponseCache } from "./utils/ResponseCache.js";
export { RetryHandler } from "./utils/RetryHandler.js";

export type {
  CreateIssuesArgs,
  CreateIssuesResult,
  CreatePRArgs,
  CreatePRResult,
  ReviewPRArgs,
  ReviewPRResult,
} from "./github/GitHubToolWrapper.js";

export type {
  SearchSAMEntityArgs,
  SearchSAMEntityResult,
  SearchContractOpportunitiesArgs,
  SearchContractOpportunitiesResult,
} from "./gsa/GSAToolWrapper.js";

export type { CredentialConfig } from "./utils/CredentialVault.js";
