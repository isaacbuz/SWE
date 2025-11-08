# System Architecture (MoE, Contract-Driven)

```
[User/Client]
   │
   ▼
[Gateway/API]──►[Router (Policy + Telemetry)]
   │                    │
   │                    ├─ Planning (OpenAI structured)
   │                    ├─ Repo Editing Swarm (Claude sub-agents)
   │                    ├─ Fast Codemod (Qwen/Granite local)
   │                    └─ QA/Compliance (policy gates)
   │
   ▼
[Contracts + State]          [Tools: GitHub, CI, Test, Lint, Sec, Diagram]
   │
   ▼
[PR + ADRs + Diagrams + Reports] → GitHub
```

**Layers** are explained with responsibilities and interfaces in this doc.
