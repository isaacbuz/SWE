# Mixture-of-Experts (MoE) Routing

- **Signals**: task type, latency/cost budget, provider quota, context length, historical pass rates.
- **Top‑k fanout**: route to 2–3 experts when beneficial (e.g., Architect + OSS coder).
- **Speculative draft & adjudication**: run a small verifier (e.g., Granite H‑Small) to check constraints and pick best.
- **Partial regeneration**: failing modules are re‑generated with failing traces.
- **Provider mesh/failover**: cascade across OpenAI/Anthropic/Google/xAI/DeepSeek/Qwen/Llama/Granite.
