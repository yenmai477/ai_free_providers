#!/usr/bin/env bash
# Local health probes. Env: GATEWAY_API_KEY, optional MODEL_ID
set -euo pipefail

GATEWAY_API_KEY="${GATEWAY_API_KEY:?GATEWAY_API_KEY required}"
MODEL_ID="${MODEL_ID:-qwen3-8b}"
LITELLM_PORT="${LITELLM_PORT:-4000}"

echo "[health] ollama"
curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null

echo "[health] litellm /v1/models"
curl -fsS -H "Authorization: Bearer ${GATEWAY_API_KEY}" \
  "http://127.0.0.1:${LITELLM_PORT}/v1/models" >/dev/null

echo "[health] ok (model expected: ${MODEL_ID})"
