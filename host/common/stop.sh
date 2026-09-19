#!/usr/bin/env bash
# Stop tunnel / LiteLLM / Ollama model processes (best-effort).
set -euo pipefail

OLLAMA_MODEL="${OLLAMA_MODEL:-}"

echo "[stop] cloudflared"
pkill -f "cloudflared tunnel" 2>/dev/null || true

echo "[stop] litellm"
pkill -f "litellm --config" 2>/dev/null || true

if [[ -n "$OLLAMA_MODEL" ]] && command -v ollama >/dev/null 2>&1; then
  echo "[stop] ollama model $OLLAMA_MODEL"
  ollama stop "$OLLAMA_MODEL" 2>/dev/null || true
fi

echo "[stop] done"
