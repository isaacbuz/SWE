```mermaid
flowchart TB
  subgraph Presentation
    UI[Streamlit/UI] --- API[REST/CLI]
  end

  subgraph Orchestration_MoE
    DEC[Task Decomposer]
    RTR[MoE Router]
    CNS[Consensus Engine]
    QG[Quality Gates]
  end

  subgraph Experts_Tools
    CEO[CEO GPT-5]
    ARCH[Architect Claude]
    VPE[VP Eng Gemini]
    CTO[Grok CTO]
    CFO[DeepSeek CFO]
    UX[UX Gemini Flash]
    SA[Solutions Arch Sonnet]
    CODER[OSS Coders (Qwen/Llama/Granite)]
    MCP[[MCP Tool Chest]]
  end

  subgraph Providers_Data
    MODELS[(Multi-Model Mesh)]
    DB[(DB & Vector Store)]
    ART[(Artifact Store)]
  end

  subgraph Ops
    OBS[Observability]
    SEC[Secrets/Policy]
    COST[Cost/Budget]
  end

  UI --> DEC --> RTR -->|parallel| CEO & ARCH & VPE & CTO & CFO & UX & SA & CODER
  CEO --> CNS
  ARCH --> CNS
  VPE --> CNS
  CTO --> CNS
  CFO --> CNS
  UX --> CNS
  SA --> CNS
  CODER --> CNS
  CNS --> QG --> MCP
  MCP -->|GitHub/CI/Deploy/Docs| MODELS
  MCP --> DB
  MCP --> ART

  OBS -. traces .- DEC
  OBS -. traces .- RTR
  SEC -. policies .- MCP
  COST -. budgets .- RTR
```
