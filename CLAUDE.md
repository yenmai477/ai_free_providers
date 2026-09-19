# Free Model Gateway

Zero-cost LLM gateway for coding clients (Claude Code, curl, etc.).

## What this repo does

```
Client → Cloudflare Quick Tunnel → LiteLLM → Ollama → exactly ONE model on Colab/HF
```

- **Host side (Colab):** `host/colab/notebook.ipynb` + `bootstrap.py` / `runtime.py` install Ollama, pull one model, start LiteLLM, open cloudflared, print READY URL.
- **Local side (PC):** `modelctl` CLI stores endpoint in `~/.modelctl/state.json` and can write Claude Code env into `~/.claude/settings.json`.
- **Config:** `config/models.yaml` (models) and `config/hosts.yaml` (GPUs) are separate registries.

## Rules for agents

- Never hard-code trycloudflare URLs or API keys into git.
- Never run multiple models in one Colab session.
- Prefer reading `README.md`, `AGENTS.md`, `docs/architecture.md` before changing architecture.
- Local package lives under `cli/modelctl/` (entry: `modelctl.main:main`).

## How to explore this codebase

Use file tools (Read / Glob / Grep). Start with:

1. `README.md`
2. `AGENTS.md`
3. `config/models.yaml`, `config/hosts.yaml`
4. `cli/modelctl/main.py`
5. `host/colab/runtime.py`
6. `gateway/templates/litellm.yaml.j2`
