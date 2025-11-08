# Integration Plan
## Providers
- **Anthropic (Claude)**: Sub‑agents, code editing with explanations, longform planning validation.
- **OpenAI**: Structured planning (SystemSpec/Backlog) in JSON mode; repo‑level refactors.
- **Google APIs**: Sheets/Drive/BigQuery for intake artifacts & data profiling (read‑only default).
- **U.S. Gov APIs**: api.data.gov/open.gsa.gov for authoritative facts.
- **GitHub**: Repo/Issues/Projects/PRs/Actions; GraphQL for Discussions.

## Rate Limits & Caching
- Exponential backoff (jitter) for 429/5xx, max retries 5; circuit breaker.
- ETag/Last‑Modified cache for gov/google; TTL per endpoint.
- Token/cost ceilings per job; degrade with cached evidence if needed.

## Security & Compliance
- OIDC for cloud auth; store runtime secrets as GitHub Actions secrets only.
- SPDX license headers; SCA + secret scans; fail PR on critical findings.
- OWASP policy checklist enforced by `seccomp_agent`.
