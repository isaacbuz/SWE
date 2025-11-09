# Diagrams (Mermaid/PlantUML)

## Multi-Layer (Mermaid)

```mermaid
flowchart TD
  U[User/Client] --> G[Gateway/API]
  G --> R[Router (Policy+Telemetry)]
  R -->|Plan| P(OpenAI Planning Lane)
  R -->|Edit| C(Claude Sub-Agents Lane)
  R -->|Codemod| O(Open-Source Local Lane)
  R -->|QA| Q(Compliance & QA)
  C --> T[Tool Surface]
  P --> T
  O --> T
  Q --> T
  T --> GH[GitHub PRs/Issues/Actions]
  subgraph Data
    CS[(Contracts Store)]
    ST[(State/Cache)]
  end
  G --> CS
  R --> ST
  T --> CS
```

## Sequence (PlantUML)

```plantuml
@startuml
actor User
User -> Gateway: Submit Build/Fix Request
Gateway -> Router: Normalize + classify task
Router -> OpenAI: Request ArchitecturePlan (structured)
OpenAI --> Router: ArchitecturePlan JSON
Router -> Claude: Execute PatchPlan via sub-agents
Claude -> Tools: read_repo/apply_patch/run_tests
Tools --> Claude: CI results + logs
Claude -> Tools: create_pr + post_discussion
Tools --> Gateway: PR URL, artifacts
Gateway --> User: Result + PR link
@enduml
```
