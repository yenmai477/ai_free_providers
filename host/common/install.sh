#!/usr/bin/env bash
# Install Ollama and cloudflared on a Linux GPU host (e.g. Colab).
set -euo pipefail

echo "[install] Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "[install] ollama already present"
fi

echo "[install] cloudflared"
if ! command -v cloudflared >/dev/null 2>&1; then
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64) CF_ARCH=amd64 ;;
    aarch64|arm64) CF_ARCH=arm64 ;;
    *) echo "Unsupported arch: $ARCH"; exit 1 ;;
  esac
  curl -fsSL \
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}" \
    -o /usr/local/bin/cloudflared
  chmod +x /usr/local/bin/cloudflared
else
  echo "[install] cloudflared already present"
fi

echo "[install] Python deps (litellm proxy)"
python -m pip install -q "litellm[proxy]" pyyaml jinja2 requests

echo "[install] done"
