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

export GATEWAY_API_KEY
export LITELLM_MASTER_KEY="${GATEWAY_API_KEY}"

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "[start] ollama serve"
  nohup ollama serve >"$OLLAMA_LOG" 2>&1 &
  sleep 3
fi

echo "[start] pull $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

echo "[start] litellm config:"
sed -n '1,40p' "$LITELLM_CONFIG" || true

# Kill any previous litellm on this port
pkill -f "litellm" 2>/dev/null || true
sleep 1
: >"$LITELLM_LOG"

echo "[start] litellm on :$LITELLM_PORT"

# Resolve litellm CLI (python -m litellm often does NOT start the proxy)
LITELLM_BIN=""
if command -v litellm >/dev/null 2>&1; then
  LITELLM_BIN="$(command -v litellm)"
else
  SCRIPTS="$("$PYTHON_BIN" -c 'import sysconfig; print(sysconfig.get_path("scripts"))')"
  if [[ -x "$SCRIPTS/litellm" ]]; then
    LITELLM_BIN="$SCRIPTS/litellm"
  fi
fi

if [[ -n "$LITELLM_BIN" ]]; then
  echo "[start] using CLI: $LITELLM_BIN"
  nohup "$LITELLM_BIN" --config "$LITELLM_CONFIG" --port "$LITELLM_PORT" --host "0.0.0.0" \
    >"$LITELLM_LOG" 2>&1 &
else
  echo "[start] using proxy_cli via $PYTHON_BIN"
  nohup "$PYTHON_BIN" -c "
from litellm.proxy.proxy_cli import run_server
import sys
sys.argv = [
    'litellm',
    '--config', r'''${LITELLM_CONFIG}''',
    '--port', '${LITELLM_PORT}',
    '--host', '0.0.0.0',
]
run_server()
" >"$LITELLM_LOG" 2>&1 &
fi

LITELLM_PID=$!
echo "[start] litellm pid=$LITELLM_PID"

# Wait briefly and verify something is listening
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${LITELLM_PORT}/health" >/dev/null 2>&1 \
     || curl -fsS -H "Authorization: Bearer ${GATEWAY_API_KEY}" \
          "http://127.0.0.1:${LITELLM_PORT}/v1/models" >/dev/null 2>&1; then
    echo "[start] litellm is up"
    exit 0
  fi
  # process died?
  if ! kill -0 "$LITELLM_PID" 2>/dev/null; then
    echo "[start] ERROR: litellm exited early. Log:" >&2
    tail -n 80 "$LITELLM_LOG" >&2 || true
    exit 1
  fi
  sleep 1
done

echo "[start] ERROR: litellm did not become ready in 30s. Log:" >&2
tail -n 80 "$LITELLM_LOG" >&2 || true
exit 1
