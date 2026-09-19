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

### modelctl (local)

```bash
pip install -e ".[dev]"

modelctl models
modelctl hosts
modelctl use colab-t4-01 qwen3-8b
modelctl connect https://xxxxx.trycloudflare.com   # from READY banner
# prints:
#   export ANTHROPIC_BASE_URL=...
#   export ANTHROPIC_API_KEY=...   # if GATEWAY_API_KEY is set in your shell

export GATEWAY_API_KEY="..."   # same key Colab printed
modelctl status                # probes /v1/models
modelctl endpoint env          # re-print exports
modelctl stop                  # clear endpoint from ~/.modelctl/state.json
```

State lives in `~/.modelctl/state.json` (override with `MODELCTL_HOME`).

**Qwen3 empty content:** LiteLLM config uses `ollama_chat/` + `think: false` so replies land in `message.content` (re-run Colab after `git pull`).

Optional client env (Anthropic-compatible adapters):

```bash
export ANTHROPIC_BASE_URL="$URL"
export ANTHROPIC_API_KEY="$GATEWAY_API_KEY"
```

Copy `.env.example` → `.env` locally; **never commit real keys or trycloudflare URLs**.

### Claude Code (custom gateway)

Claude Code talks **Anthropic Messages API** (`/v1/messages`) via LiteLLM. After Colab is READY:

```powershell
$env:GATEWAY_API_KEY = "<key from Colab>"
modelctl connect https://xxxxx.trycloudflare.com
modelctl claude setup    # writes %USERPROFILE%\.claude\settings.json
```

Then restart the terminal and run:

```powershell
claude
# or pin model:
claude --model qwen3-8b-claude
```

Inside Claude Code: `/model` → pick gateway model (`*-claude` / From gateway).

Verify Messages API:

```powershell
curl.exe -sS "$env:ANTHROPIC_BASE_URL/v1/messages" `
  -H "Authorization: Bearer $env:GATEWAY_API_KEY" `
  -H "Content-Type: application/json" `
  -H "anthropic-version: 2023-06-01" `
  -d "{\"model\":\"qwen3-8b-claude\",\"max_tokens\":64,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}"
```

**Re-run Colab after `git pull`** so LiteLLM regenerates aliases (`qwen3-8b-claude` + default Claude model ids → same Ollama backend).

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
| `cli/modelctl/` | CLI + shared services |
| `host/colab/` | Notebook + runtime |
| `host/common/` | Install/start/stop/tunnel scripts |
| `gateway/templates/` | LiteLLM Jinja template |

See [docs/architecture.md](docs/architecture.md) and [AGENTS.md](AGENTS.md).
