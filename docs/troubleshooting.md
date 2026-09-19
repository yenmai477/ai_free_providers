# Troubleshooting

## `install.sh` exit status 1 (Colab)

Re-run the READY cell after pulling the latest scripts. The bootstrap now prints full `[install]` logs.

Typical causes:
- **cloudflared Permission denied** writing `/usr/local/bin` — fixed by installing to `~/.local/bin`
- **pip / Python 3.13** — install uses the notebook’s `sys.executable` and `--break-system-packages` when needed
- **Ollama install network flake** — re-run the cell; Ollama download is large

Manual recovery in a Colab cell:

```python
import os, sys
os.environ["PYTHON_BIN"] = sys.executable
!bash /content/ai_free_providers/host/common/install.sh
```

Then:

```python
result = runtime.run(..., skip_install=True)
```

## `config/models.yaml` not found

Clone/upload the full repo into Colab. Set `REPO_ROOT` in the notebook if needed.

## nvidia-smi fails

Enable a GPU runtime: **Runtime → Change runtime type → T4**.

## Model VRAM errors

Lower `CONTEXT`, or pick a smaller model (after Phase 1). T4 usable budget is ~13 GB.

## No trycloudflare URL

Check `/tmp/cloudflared.log`. Re-run the tunnel cell; Quick Tunnels can take ~30–60s.

## LiteLLM 401

Use the same `GATEWAY_API_KEY` printed by the READY banner in the `Authorization: Bearer` header.

## Ollama pull slow

First pull of `qwen3:8b` downloads several GB; wait for the health pipeline to finish.
