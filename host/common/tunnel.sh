#!/usr/bin/env bash
# Start Cloudflare quick tunnel to LiteLLM. Env: LITELLM_PORT
set -euo pipefail

LITELLM_PORT="${LITELLM_PORT:-4000}"
CLOUDFLARED_LOG="${CLOUDFLARED_LOG:-/tmp/cloudflared.log}"

echo "[tunnel] cloudflared -> http://127.0.0.1:${LITELLM_PORT}"
: >"$CLOUDFLARED_LOG"
nohup cloudflared tunnel --url "http://127.0.0.1:${LITELLM_PORT}" \
  >"$CLOUDFLARED_LOG" 2>&1 &

echo "[tunnel] log: $CLOUDFLARED_LOG"
