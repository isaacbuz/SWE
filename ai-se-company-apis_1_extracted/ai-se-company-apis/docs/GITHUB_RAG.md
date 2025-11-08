# Public GitHub Repos for Prompt‑Domain RAG

**Intent**
- Treat *high‑quality repos* as living corpora for domain prompts: style guides, ADRs, security checklists, API usage patterns.
- Build a lightweight **Corpus Builder** that:
  1) Crawls `README.md`, `/docs`, `/adr`, `/CONTRIBUTING.md`, `/SECURITY.md`
  2) Normalizes → chunks → embeds
  3) Stores into your vector DB (or local JSONL for demo)

**Quality Filters**
- Stars > 2k, commits in last 180 days, non‑archived
- Prefer well-known orgs; allowlists in `providers.yaml`

**RAG Patterns**
- **Plan‑time**: Retrieve K=20 chunks for planning prompts; include provenance.
- **Review‑time**: Retrieve policy chunks relevant to diff paths; improve code reviews.
- **Blue/Green**: Maintain two corpora and A/B test retrieval signals.

**Security**
- Public content only. Respect licenses. Persist `source_url`, `license`, `sha` per chunk.
