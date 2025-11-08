```mermaid
flowchart TD
  A[User Brief] --> R[Router]
  R -->|gov| GSA[Gov API Fetcher]
  R -->|sheets| GGL[Google Intake]
  R --> RAG[Design RAG]
  GSA --> E[Evidence Fabric]
  GGL --> E
  RAG --> E
  E --> P[[OpenAI Planner
SystemSpec + Backlog (JSON)]]
  P --> C1[Claude Impl Agent
PatchPlan + Tests + CI + ADR]
  C1 --> S[Sec/Compliance Agent]
  S -->|pass| QA[QA Agent]
  QA -->|ready| D[Delivery Agent → GitHub]
  S -->|fail| C1
  QA -->|revise| C1
```