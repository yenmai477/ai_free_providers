#!/usr/bin/env bash
# Start Ollama + LiteLLM for a single model. Env: OLLAMA_MODEL, GATEWAY_API_KEY, LITELLM_CONFIG
set -euo pipefail

BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
export PATH="$BIN_DIR:/usr/local/bin:$PATH"

# Colab: prefer system NVIDIA libraries
if [[ -d /usr/lib64-nvidia ]]; then
  export LD_LIBRARY_PATH="/usr/lib64-nvidia${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

OLLAMA_LOG="${OLLAMA_LOG:-/tmp/ollama.log}"
LITELLM_LOG="${LITELLM_LOG:-/tmp/litellm.log}"
LITELLM_CONFIG="${LITELLM_CONFIG:-/tmp/litellm.yaml}"
LITELLM_PORT="${LITELLM_PORT:-4000}"
OLLAMA_MODEL="${OLLAMA_MODEL:?OLLAMA_MODEL required}"
GATEWAY_API_KEY="${GATEWAY_API_KEY:?GATEWAY_API_KEY required}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "[start] ollama serve"
  nohup ollama serve >"$OLLAMA_LOG" 2>&1 &
  sleep 3
fi

echo "[start] pull $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

echo "[start] litellm on :$LITELLM_PORT"
export GATEWAY_API_KEY
# Prefer module entry (works even when scripts/ not on PATH in Colab).
if "$PYTHON_BIN" -c "import litellm" >/dev/null 2>&1; then
  nohup "$PYTHON_BIN" -m litellm --config "$LITELLM_CONFIG" --port "$LITELLM_PORT" \
    >"$LITELLM_LOG" 2>&1 &
else
  nohup litellm --config "$LITELLM_CONFIG" --port "$LITELLM_PORT" \
    >"$LITELLM_LOG" 2>&1 &
fi

echo "[start] backend processes launched"
