# U.S. Government APIs (GSA / api.data.gov) Integration

**Targets**

- `open.gsa.gov/api` catalogs (e.g., USASpending, SAM.gov derivatives, FOIA, digital.gov datasets).
- Many services are proxied via **api.data.gov** with a unified API key.

**Design**

- Central `GovApiClient` with:
  - Base URL + per-endpoint key injection (`X-API-Key` header or `api_key` query).
  - **Schema adapters**: Convert raw JSON → domain contracts (`Agency`, `Award`, `Vendor`, etc.).
  - **Pagination helpers** and **backoff** on 429/5xx.
  - **Compliance**: Store provenance (endpoint, params, time, hash) inside contract metadata.

**Use Cases**

- Compliance-aware planning: derive constraints (e.g., FedRAMP, Section 508) as **Policy Facts**
- Domain prompting: include authoritative definitions and thresholds in plan validation
- Public-service apps: e.g., grant finder, procurement analytics, civic dashboards

**Notes**

- Some datasets are **stale**; always track `last_updated` and include in prompt context.
- Respect TOS and rate limits; enable **router policy** to throttle high-cost flows.
