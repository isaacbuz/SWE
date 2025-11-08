# Diagrams (Mermaid + PlantUML)

## Mermaid — External API Lane (Google + GSA + GitHub RAG)

```mermaid
flowchart TD
  U[User / Ops Console] -->|Prompt / Job| R[MoE Router]
  R -->|Policy: allow google| GGL[Google Connector]
  R -->|Policy: allow gsa| GSA[GSA Connector]
  R -->|Policy: allow github| GHRAG[GitHub Corpus Builder / RAG]

  GGL -->|Sheets/Drive/BigQuery| NORM1[Normalizer → Contracts]
  GSA -->|JSON APIs| NORM2[Normalizer → Contracts]
  GHRAG -->|Chunks| VDB[(Vector Store)]

  subgraph Planning Lane
  PLAN[Planner (Claude/OpenAI)] --> SPEC[SystemSpec Contract]
  SPEC --> EXEC[Exec Lane (Sub‑agents / Tools)]
  end

  NORM1 --> PLAN
  NORM2 --> PLAN
  VDB --> PLAN

  EXEC --> PR[GitHub PR Draft]
  PR --> CI[GitHub Actions / CI]
  CI --> MERGE[Merge / Release]
```

## PlantUML — Connectors and Policies

```plantuml
@startuml
skinparam packageStyle rectangle

package "Policy Layer" {
  class RouterPolicy {
    +allow_google: bool
    +allow_gsa: bool
    +allow_github_rag: bool
    +max_tokens:int
    +rate_limits: Map
  }
  class Router {
    +route(job): Path
  }
}

package "Connectors" {
  interface Connector { +fetch(query): Contract }
  class GoogleConnector implements Connector
  class GsaConnector implements Connector
  class GitHubCorpusBuilder

  GoogleConnector --> "uses" OAuth
  GsaConnector --> "uses" ApiKey
}

package "Contracts" {
  class SystemSpec
  class Backlog
  class PolicyFacts
}

RouterPolicy --> Router
Router --> GoogleConnector
Router --> GsaConnector
Router --> GitHubCorpusBuilder
GoogleConnector --> SystemSpec
GsaConnector --> PolicyFacts
GitHubCorpusBuilder --> SystemSpec

@enduml
```
