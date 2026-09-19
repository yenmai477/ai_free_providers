# Free Model Gateway

Zero-cost path for coding clients:

```
Client → Cloudflare Quick Tunnel → LiteLLM → Ollama → exactly one model
```

Phase 1 vertical slice: **Colab T4 → Ollama → qwen3-8b → LiteLLM → tunnel → curl**.

## Quick start (Colab)

1. Clone or upload this repo into the Colab runtime (must include `config/`).
2. Open [`host/colab/notebook.ipynb`](host/colab/notebook.ipynb).
3. Set `MODEL=qwen3-8b`, `CONTEXT`, `HOST_ID`, then **Run all**.
4. Wait for the **MODEL READY** banner and copy the printed URL + `GATEWAY_API_KEY`.

## Verify from your PC

```bash
export URL="https://xxxxx.trycloudflare.com"   # from Colab READY banner
export GATEWAY_API_KEY="..."                   # printed once in Colab

curl -sS -H "Authorization: Bearer $GATEWAY_API_KEY" "$URL/v1/models"

curl -sS -H "Authorization: Bearer $GATEWAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-8b","messages":[{"role":"user","content":"hi"}],"max_tokens":32}' \
  "$URL/v1/chat/completions"
```

Optional client env (Anthropic-compatible adapters):

```bash
export ANTHROPIC_BASE_URL="$URL"
export ANTHROPIC_API_KEY="$GATEWAY_API_KEY"
```

Copy `.env.example` → `.env` locally; **never commit real keys or trycloudflare URLs**.

## Local development

```bash
pip install -e ".[dev]"
pytest
```

## Layout

| Path | Role |
|------|------|
| `config/models.yaml` | Model registry |
| `config/hosts.yaml` | Host registry |
| `config/settings.yaml` | Ports, VRAM profiles |
| `cli/modelctl/` | Shared services (+ CLI stub) |
| `host/colab/` | Notebook + runtime |
| `host/common/` | Install/start/stop/tunnel scripts |
| `gateway/templates/` | LiteLLM Jinja template |

See [docs/architecture.md](docs/architecture.md) and [AGENTS.md](AGENTS.md).
