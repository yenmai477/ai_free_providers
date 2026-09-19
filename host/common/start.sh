#!/usr/bin/env bash
# Start Ollama + LiteLLM for a single model. Env: OLLAMA_MODEL, GATEWAY_API_KEY, LITELLM_CONFIG
set -euo pipefail

OLLAMA_LOG="${OLLAMA_LOG:-/tmp/ollama.log}"
LITELLM_LOG="${LITELLM_LOG:-/tmp/litellm.log}"
LITELLM_CONFIG="${LITELLM_CONFIG:-/tmp/litellm.yaml}"
LITELLM_PORT="${LITELLM_PORT:-4000}"
OLLAMA_MODEL="${OLLAMA_MODEL:?OLLAMA_MODEL required}"
GATEWAY_API_KEY="${GATEWAY_API_KEY:?GATEWAY_API_KEY required}"

if ! pgrep -x ollama >/dev/null 2>&1; then
  echo "[start] ollama serve"
  nohup ollama serve >"$OLLAMA_LOG" 2>&1 &
  sleep 2
fi

echo "[start] pull $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

echo "[start] litellm on :$LITELLM_PORT"
export GATEWAY_API_KEY
nohup litellm --config "$LITELLM_CONFIG" --port "$LITELLM_PORT" \
  >"$LITELLM_LOG" 2>&1 &

echo "[start] backend processes launched"
