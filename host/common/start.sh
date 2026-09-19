#!/usr/bin/env bash
# Start Ollama + LiteLLM for a single model.
# Env: OLLAMA_MODEL, GATEWAY_API_KEY, LITELLM_CONFIG, PYTHON_BIN
set -uo pipefail

BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SCRIPTS_DIR="$("$PYTHON_BIN" -c 'import sysconfig; print(sysconfig.get_path("scripts"))' 2>/dev/null || true)"
export PATH="$BIN_DIR:${SCRIPTS_DIR}:/usr/local/bin:$PATH"

if [[ -d /usr/lib64-nvidia ]]; then
  export LD_LIBRARY_PATH="/usr/lib64-nvidia${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

OLLAMA_LOG="${OLLAMA_LOG:-/tmp/ollama.log}"
LITELLM_LOG="${LITELLM_LOG:-/tmp/litellm.log}"
LITELLM_CONFIG="${LITELLM_CONFIG:-/tmp/litellm.yaml}"
LITELLM_PORT="${LITELLM_PORT:-4000}"
OLLAMA_MODEL="${OLLAMA_MODEL:?OLLAMA_MODEL required}"
GATEWAY_API_KEY="${GATEWAY_API_KEY:?GATEWAY_API_KEY required}"

export GATEWAY_API_KEY
export LITELLM_MASTER_KEY="${GATEWAY_API_KEY}"
export CONFIG_FILE_PATH="${LITELLM_CONFIG}"

dump_logs() {
  echo "======== /tmp litellm.log (tail) ========" >&2
  if [[ -f "$LITELLM_LOG" ]]; then
    tail -n 100 "$LITELLM_LOG" >&2
  else
    echo "(no litellm log)" >&2
  fi
  echo "======== /tmp ollama.log (tail) ========" >&2
  if [[ -f "$OLLAMA_LOG" ]]; then
    tail -n 40 "$OLLAMA_LOG" >&2
  else
    echo "(no ollama log)" >&2
  fi
}

echo "[start] PATH=$PATH"
echo "[start] PYTHON_BIN=$PYTHON_BIN"
echo "[start] which ollama=$(command -v ollama || echo MISSING)"
echo "[start] which litellm=$(command -v litellm || echo MISSING)"

if ! command -v ollama >/dev/null 2>&1; then
  echo "[start] ERROR: ollama not on PATH" >&2
  dump_logs
  exit 1
fi

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "[start] ollama serve"
  nohup ollama serve >"$OLLAMA_LOG" 2>&1 &
  sleep 3
fi

echo "[start] wait for ollama API…"
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    echo "[start] ollama API ready"
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    echo "[start] ERROR: ollama API not ready" >&2
    dump_logs
    exit 1
  fi
  sleep 1
done

echo "[start] pull $OLLAMA_MODEL"
if ! ollama pull "$OLLAMA_MODEL"; then
  echo "[start] ERROR: ollama pull failed" >&2
  dump_logs
  exit 1
fi

if [[ ! -f "$LITELLM_CONFIG" ]]; then
  echo "[start] ERROR: missing config $LITELLM_CONFIG" >&2
  exit 1
fi
echo "[start] litellm config:"
sed -n '1,40p' "$LITELLM_CONFIG" || true

pkill -f "[l]itellm" 2>/dev/null || true
fuser -k "${LITELLM_PORT}/tcp" 2>/dev/null || true
sleep 1
: >"$LITELLM_LOG"

"$PYTHON_BIN" -c "import uvicorn, fastapi, litellm" 2>/dev/null || {
  echo "[start] installing litellm proxy deps…"
  "$PYTHON_BIN" -m pip install -q --break-system-packages 'litellm[proxy]' uvicorn fastapi || \
    "$PYTHON_BIN" -m pip install -q 'litellm[proxy]' uvicorn fastapi || true
}

echo "[start] litellm on :$LITELLM_PORT"

# IMPORTANT: only the PID may go to stdout from this function; logs → stderr
launch_litellm() {
  local mode="$1"
  echo "[start] launch mode: $mode" >&2
  case "$mode" in
    cli)
      local bin
      bin="$(command -v litellm || true)"
      if [[ -z "$bin" && -x "${SCRIPTS_DIR}/litellm" ]]; then
        bin="${SCRIPTS_DIR}/litellm"
      fi
      if [[ -z "$bin" ]]; then
        echo "[start] litellm CLI not found" >&2
        return 1
      fi
      echo "[start] CLI=$bin" >&2
      nohup "$bin" --config "$LITELLM_CONFIG" --port "$LITELLM_PORT" --host "0.0.0.0" \
        >"$LITELLM_LOG" 2>&1 &
      echo $!
      return 0
      ;;
    proxy_cli)
      nohup "$PYTHON_BIN" -c "
import sys
from litellm.proxy.proxy_cli import run_server
sys.argv = ['litellm', '--config', r'''${LITELLM_CONFIG}''', '--port', '${LITELLM_PORT}', '--host', '0.0.0.0']
run_server()
" >"$LITELLM_LOG" 2>&1 &
      echo $!
      return 0
      ;;
    uvicorn)
      nohup "$PYTHON_BIN" -c "
import os, uvicorn
os.environ['LITELLM_MASTER_KEY'] = os.environ.get('LITELLM_MASTER_KEY', '')
os.environ['CONFIG_FILE_PATH'] = r'''${LITELLM_CONFIG}'''
from litellm.proxy.proxy_server import app
uvicorn.run(app, host='0.0.0.0', port=int('${LITELLM_PORT}'))
" >"$LITELLM_LOG" 2>&1 &
      echo $!
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

for mode in cli proxy_cli uvicorn; do
  : >"$LITELLM_LOG"
  if ! LITELLM_PID="$(launch_litellm "$mode")"; then
    echo "[start] mode $mode unavailable"
    continue
  fi
  # sanitize: PID must be digits only
  if ! [[ "$LITELLM_PID" =~ ^[0-9]+$ ]]; then
    echo "[start] ERROR: bad pid capture for mode=$mode: '$LITELLM_PID'" >&2
    continue
  fi
  echo "[start] litellm pid=$LITELLM_PID (mode=$mode)"

  ready=0
  for i in $(seq 1 90); do
    if curl -fsS "http://127.0.0.1:${LITELLM_PORT}/health" >/dev/null 2>&1 \
       || curl -fsS -H "Authorization: Bearer ${GATEWAY_API_KEY}" \
            "http://127.0.0.1:${LITELLM_PORT}/v1/models" >/dev/null 2>&1 \
       || curl -fsS "http://127.0.0.1:${LITELLM_PORT}/v1/models" >/dev/null 2>&1; then
      echo "[start] litellm is up (mode=$mode)"
      ready=1
      break
    fi
    if ! kill -0 "$LITELLM_PID" 2>/dev/null; then
      echo "[start] mode $mode exited early"
      tail -n 60 "$LITELLM_LOG" || true
      break
    fi
    sleep 1
  done

  if [[ "$ready" -eq 1 ]]; then
    exit 0
  fi
  pkill -f "[l]itellm" 2>/dev/null || true
  kill "$LITELLM_PID" 2>/dev/null || true
  fuser -k "${LITELLM_PORT}/tcp" 2>/dev/null || true
  sleep 1
done

echo "[start] ERROR: all litellm launch modes failed" >&2
dump_logs
exit 1
