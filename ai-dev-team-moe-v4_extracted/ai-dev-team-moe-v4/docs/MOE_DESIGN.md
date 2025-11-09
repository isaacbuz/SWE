# Mixture of Experts (MoE) Design

- Declarative registry maps **roles → preferred models + fallbacks**.
- Router factors cost caps, vendor diversity, and task hints.
- Each agent receives a `suggested_model` id and invokes the appropriate API.
- Add dynamic signals later (latency, recent failures, budget left).

MoE signals (initial):

- Cost cap check
- Context window requirement estimate
- Vendor diversity toggle
