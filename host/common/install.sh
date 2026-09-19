#!/usr/bin/env bash
# Install Ollama and cloudflared on a Linux GPU host (e.g. Colab).
set -euo pipefail

BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"
export PATH="$BIN_DIR:/usr/local/bin:$PATH"

# Prefer the interpreter that launched the notebook (passed from bootstrap).
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

echo "[install] PATH bin dir: $BIN_DIR"
echo "[install] Python: $PYTHON_BIN ($("$PYTHON_BIN" -V 2>&1 || true))"

echo "[install] Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
  # Official installer usually puts binary in /usr/local/bin; ensure PATH sees it.
  hash -r 2>/dev/null || true
  if ! command -v ollama >/dev/null 2>&1; then
    echo "[install] ERROR: ollama not on PATH after install" >&2
    exit 1
  fi
else
  echo "[install] ollama already present: $(command -v ollama)"
fi

echo "[install] cloudflared"
if ! command -v cloudflared >/dev/null 2>&1; then
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64) CF_ARCH=amd64 ;;
    aarch64|arm64) CF_ARCH=arm64 ;;
    *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;;
  esac
  CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}"
  CF_DEST="$BIN_DIR/cloudflared"
  echo "[install] downloading cloudflared → $CF_DEST"
  if ! curl -fsSL "$CF_URL" -o "$CF_DEST"; then
    echo "[install] ERROR: failed to download cloudflared" >&2
    exit 1
  fi
  chmod +x "$CF_DEST"
  # Best-effort system path if we have write access (ignore failure).
  if [[ -w /usr/local/bin ]] || [[ $(id -u) -eq 0 ]]; then
    cp -f "$CF_DEST" /usr/local/bin/cloudflared 2>/dev/null || true
  fi
else
  echo "[install] cloudflared already present: $(command -v cloudflared)"
fi

echo "[install] Python deps (litellm proxy)"
PIP_FLAGS=(-q)
# Colab / PEP 668: allow user installs when needed
if "$PYTHON_BIN" -m pip install --help 2>/dev/null | grep -q break-system-packages; then
  PIP_FLAGS+=(--break-system-packages)
fi
if ! "$PYTHON_BIN" -m pip install "${PIP_FLAGS[@]}" "litellm[proxy]" pyyaml jinja2 requests; then
  echo "[install] retry pip without [proxy] extras…" >&2
  "$PYTHON_BIN" -m pip install "${PIP_FLAGS[@]}" litellm pyyaml jinja2 requests uvicorn fastapi
fi

# Ensure litellm CLI is importable / on PATH
if ! "$PYTHON_BIN" -c "import litellm" 2>/dev/null; then
  echo "[install] ERROR: litellm import failed" >&2
  exit 1
fi

echo "[install] done"
echo "[install] ollama=$(command -v ollama)"
echo "[install] cloudflared=$(command -v cloudflared)"
