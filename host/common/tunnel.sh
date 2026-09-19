#!/usr/bin/env bash
# Start Cloudflare quick tunnel to LiteLLM. Env: LITELLM_PORT
set -euo pipefail

BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
export PATH="$BIN_DIR:/usr/local/bin:$PATH"

LITELLM_PORT="${LITELLM_PORT:-4000}"
CLOUDFLARED_LOG="${CLOUDFLARED_LOG:-/tmp/cloudflared.log}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "[tunnel] ERROR: cloudflared not found on PATH=$PATH" >&2
  exit 1
fi

echo "[tunnel] cloudflared -> http://127.0.0.1:${LITELLM_PORT}"
: >"$CLOUDFLARED_LOG"
nohup cloudflared tunnel --url "http://127.0.0.1:${LITELLM_PORT}" \
  >"$CLOUDFLARED_LOG" 2>&1 &

echo "[tunnel] log: $CLOUDFLARED_LOG"
