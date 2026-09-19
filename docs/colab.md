# Colab host

1. Upload or clone the repo into `/content/...` so `config/models.yaml` exists.
2. Open `notebook.ipynb`, confirm `MODEL=qwen3-8b`.
3. Runtime → Run all.
4. Copy the READY endpoint and `GATEWAY_API_KEY` for local curl.

Runtime logic lives in `bootstrap.py` and `runtime.py`.
