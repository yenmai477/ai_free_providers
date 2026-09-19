# Free Model Gateway

## Architecture

This project provides a zero-cost model gateway
for Claude Code and coding clients.

Architecture:

Client
-> Cloudflare Tunnel
-> LiteLLM
-> Ollama
-> exactly one selected model

## Rules

- Never run multiple models simultaneously.
- Never hard-code a Cloudflare URL.
- Model definitions belong in config/models.yaml.
- Host definitions belong in config/hosts.yaml.
- Never put API keys into git.
- Validate GPU VRAM before downloading a model.
- Validate model health before exposing the endpoint.
- Keep Colab bootstrap self-contained.
- Do not introduce a central always-on server for MVP.

## Model lifecycle

One Colab runtime selects exactly one model.

The model is selected before startup.

The notebook must not download or load
unselected models.

## Phase 1 focus

Vertical slice only: Colab T4 → Ollama → qwen3-8b → LiteLLM → Cloudflare Quick Tunnel → curl e2e.

## Testing

Run:

```
pytest
```

before committing changes.
