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

## Phase focus

Any registry model allowed on the selected host (one model per Colab session).
Default smoke path: Colab T4 → qwen3-8b → LiteLLM → Cloudflare → curl / Claude Code.

## Testing

Run:

```
pytest
```

before committing changes.
