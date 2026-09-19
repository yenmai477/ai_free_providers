#!/usr/bin/env bash
# Install Ollama and cloudflared on a Linux GPU host (e.g. Colab).
# Prefer bootstrap.install_all() from Python; this script is a fallback.
set +e
set -u

BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"
export PATH="$BIN_DIR:/usr/local/bin:$PATH"

# Colab NVIDIA libs
if [[ -d /usr/lib64-nvidia ]]; then
  export LD_LIBRARY_PATH="/usr/lib64-nvidia${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || PYTHON_BIN=python

echo "[install] PATH bin dir: $BIN_DIR"
echo "[install] Python: $PYTHON_BIN ($("$PYTHON_BIN" -V 2>&1 || true))"

FAILED=0

echo "[install] Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
  hash -r 2>/dev/null || true
fi
if ! command -v ollama >/dev/null 2>&1; then
  echo "[install] install.sh did not place ollama; trying tar.zst…"
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64) ASSET=ollama-linux-amd64.tar.zst ;;
    aarch64|arm64) ASSET=ollama-linux-arm64.tar.zst ;;
    *) echo "Unsupported arch: $ARCH" >&2; FAILED=1; ASSET="" ;;
  esac
  if [[ -n "$ASSET" ]]; then
    curl -fsSL "https://ollama.com/download/${ASSET}" -o "/tmp/${ASSET}"
    if [[ -w /usr ]] || [[ $(id -u) -eq 0 ]]; then
      PREFIX=/usr
    else
      PREFIX="$HOME/.local"
      mkdir -p "$PREFIX"
    fi
    if ! tar -x --zstd -f "/tmp/${ASSET}" -C "$PREFIX" 2>/dev/null; then
      if command -v zstd >/dev/null 2>&1; then
        zstd -d -c "/tmp/${ASSET}" | tar -x -C "$PREFIX"
      else
        apt-get update -qq && apt-get install -y -qq zstd
        zstd -d -c "/tmp/${ASSET}" | tar -x -C "$PREFIX"
      fi
    fi
    export PATH="$PREFIX/bin:$PATH"
  fi
fi
if ! command -v ollama >/dev/null 2>&1; then
  echo "[install] ERROR: ollama not on PATH after install" >&2
  FAILED=1
else
  echo "[install] ollama: $(command -v ollama)"
fi

echo "[install] cloudflared"
if ! command -v cloudflared >/dev/null 2>&1; then
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64) CF_ARCH=amd64 ;;
    aarch64|arm64) CF_ARCH=arm64 ;;
    *) echo "Unsupported arch: $ARCH" >&2; FAILED=1; CF_ARCH="" ;;
  esac
  if [[ -n "${CF_ARCH}" ]]; then
    CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}"
    CF_DEST="$BIN_DIR/cloudflared"
    echo "[install] downloading cloudflared → $CF_DEST"
    if curl -fsSL "$CF_URL" -o "$CF_DEST"; then
      chmod +x "$CF_DEST"
    else
      echo "[install] ERROR: failed to download cloudflared" >&2
      FAILED=1
    fi
  fi
else
  echo "[install] cloudflared already present: $(command -v cloudflared)"
fi

echo "[install] Python deps (litellm proxy)"
PIP_FLAGS=(-q)
if "$PYTHON_BIN" -m pip install --help 2>/dev/null | grep -q break-system-packages; then
  PIP_FLAGS+=(--break-system-packages)
fi
if ! "$PYTHON_BIN" -m pip install "${PIP_FLAGS[@]}" "litellm[proxy]" pyyaml jinja2 requests; then
  echo "[install] retry pip without [proxy] extras…" >&2
  if ! "$PYTHON_BIN" -m pip install "${PIP_FLAGS[@]}" litellm pyyaml jinja2 requests uvicorn fastapi; then
    echo "[install] ERROR: pip install failed" >&2
    FAILED=1
  fi
fi

if ! "$PYTHON_BIN" -c "import litellm" 2>/dev/null; then
  echo "[install] ERROR: litellm import failed" >&2
  FAILED=1
fi

if [[ "$FAILED" -ne 0 ]]; then
  echo "[install] FAILED" >&2
  exit 1
fi

echo "[install] done"
echo "[install] ollama=$(command -v ollama)"
echo "[install] cloudflared=$(command -v cloudflared)"
exit 0
