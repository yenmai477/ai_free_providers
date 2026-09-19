# Colab host

1. Upload or clone the repo into `/content/...` so `config/models.yaml` exists.
2. Open `notebook.ipynb`, pick `MODEL` / `CONTEXT` / `HOST_ID` (must be in host allow-list).
3. Runtime → Run all (Restart runtime when switching models).
4. Copy the READY endpoint and `GATEWAY_API_KEY` for local `modelctl connect`.

Runtime logic lives in `bootstrap.py` and `runtime.py`. See `docs/models.md` for VRAM/context tips.
