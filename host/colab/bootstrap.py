"""Colab bootstrap: path setup, installs, secrets."""

from __future__ import annotations

import os
import platform
import secrets
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Locate repo root that contains config/models.yaml."""
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "config" / "models.yaml").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find repo root (config/models.yaml). "
        "Upload or clone the free-model-gateway repo into the Colab runtime."
    )


def ensure_python_path(repo_root: Path) -> None:
    cli = str(repo_root / "cli")
    if cli not in sys.path:
        sys.path.insert(0, cli)


def ensure_gateway_api_key() -> str:
    key = os.environ.get("GATEWAY_API_KEY", "").strip()
    if not key:
        key = secrets.token_urlsafe(32)
        os.environ["GATEWAY_API_KEY"] = key
        print("[bootstrap] Generated GATEWAY_API_KEY for this session")
    return key


def _bin_dir() -> Path:
    path = Path(os.environ.get("BIN_DIR", Path.home() / ".local" / "bin"))
    path.mkdir(parents=True, exist_ok=True)
    os.environ["PATH"] = f"{path}:/usr/local/bin:{os.environ.get('PATH', '')}"
    return path


def _run(cmd: list[str], *, check: bool = True, env: dict | None = None) -> int:
    print(f"[bootstrap] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env or os.environ.copy())
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")
    return result.returncode


def _which(name: str) -> str | None:
    return shutil.which(name)


def _cloudflared_arch() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "amd64"
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    raise RuntimeError(f"Unsupported arch for cloudflared: {machine}")


def _download(url: str, dest: Path) -> None:
    print(f"[bootstrap] download {url} → {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def install_ollama() -> None:
    if _which("ollama"):
        print(f"[bootstrap] ollama already present: {_which('ollama')}")
        return

    print("[bootstrap] Installing Ollama via official install.sh…")
    # Do not use pipefail semantics that abort on installer warnings.
    script = "curl -fsSL https://ollama.com/install.sh | sh"
    rc = subprocess.run(["bash", "-c", script]).returncode
    if rc == 0 and _which("ollama"):
        print(f"[bootstrap] ollama installed: {_which('ollama')}")
        return

    print("[bootstrap] Official installer failed; trying direct binary…")
    bin_dir = _bin_dir()
    # Stable-ish release asset name used by Ollama Linux packages
    tgz = Path("/tmp/ollama-linux.tgz")
    url = "https://ollama.com/download/ollama-linux-amd64.tgz"
    try:
        _download(url, tgz)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Failed to install Ollama (install.sh and direct download both failed). "
            f"Last error: {exc}"
        ) from exc

    extract_dir = Path("/tmp/ollama-extract")
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)
    _run(["tar", "-xzf", str(tgz), "-C", str(extract_dir)])
    # Binary may be at extract_dir/bin/ollama or extract_dir/ollama
    candidates = list(extract_dir.rglob("ollama"))
    binary = next((c for c in candidates if c.is_file()), None)
    if binary is None:
        raise RuntimeError("ollama binary not found inside downloaded archive")
    dest = bin_dir / "ollama"
    shutil.copy2(binary, dest)
    dest.chmod(dest.stat().st_mode | 0o111)
    if not _which("ollama"):
        raise RuntimeError("ollama still not on PATH after manual install")
    print(f"[bootstrap] ollama installed: {_which('ollama')}")


def install_cloudflared() -> None:
    if _which("cloudflared"):
        print(f"[bootstrap] cloudflared already present: {_which('cloudflared')}")
        return

    bin_dir = _bin_dir()
    dest = bin_dir / "cloudflared"
    arch = _cloudflared_arch()
    url = (
        "https://github.com/cloudflare/cloudflared/releases/latest/download/"
        f"cloudflared-linux-{arch}"
    )
    _download(url, dest)
    dest.chmod(dest.stat().st_mode | 0o111)
    if not _which("cloudflared"):
        raise RuntimeError("cloudflared not on PATH after install")
    print(f"[bootstrap] cloudflared installed: {_which('cloudflared')}")


def install_python_deps() -> None:
    py = sys.executable
    print(f"[bootstrap] pip via {py} ({sys.version.split()[0]})")
    base = [py, "-m", "pip", "install", "-q"]
    # Detect PEP 668 / Colab
    help_text = subprocess.run(
        [py, "-m", "pip", "install", "--help"],
        capture_output=True,
        text=True,
    ).stdout
    if "break-system-packages" in help_text:
        base.append("--break-system-packages")

    try:
        _run([*base, "litellm[proxy]", "pyyaml", "jinja2", "requests"])
    except RuntimeError:
        print("[bootstrap] litellm[proxy] failed; retrying minimal deps…")
        _run(
            [
                *base,
                "litellm",
                "pyyaml",
                "jinja2",
                "requests",
                "uvicorn",
                "fastapi",
            ]
        )

    result = subprocess.run([py, "-c", "import litellm"])
    if result.returncode != 0:
        raise RuntimeError("litellm import failed after pip install")
    print("[bootstrap] litellm OK")


def install_all(repo_root: Path | None = None) -> None:
    """Install Ollama, cloudflared, and Python deps (Colab-safe)."""
    _ = repo_root  # reserved for future use
    _bin_dir()
    print("[bootstrap] === install start ===")
    install_ollama()
    install_cloudflared()
    install_python_deps()
    print("[bootstrap] === install done ===")
    print(f"[bootstrap] ollama={_which('ollama')}")
    print(f"[bootstrap] cloudflared={_which('cloudflared')}")


def run_install_script(repo_root: Path) -> None:
    """Backward-compatible entry used by runtime.run()."""
    if repo_root:
        chmod_scripts(repo_root)
    # Prefer Python installer (clear per-step errors). Bash script kept as fallback.
    try:
        install_all(repo_root)
        return
    except Exception as py_exc:  # noqa: BLE001
        print(f"[bootstrap] Python installer failed: {py_exc}")
        print("[bootstrap] Falling back to install.sh…")

    script = repo_root / "host" / "common" / "install.sh"
    env = os.environ.copy()
    env["PYTHON_BIN"] = sys.executable
    env["BIN_DIR"] = str(_bin_dir())
    env["PATH"] = f"{env['BIN_DIR']}:/usr/local/bin:{env.get('PATH', '')}"
    print(f"[bootstrap] Running {script}")
    result = subprocess.run(["bash", str(script)], env=env)
    if result.returncode != 0:
        raise RuntimeError(
            f"Both Python installer and install.sh failed "
            f"(bash exit {result.returncode}). See logs above."
        )


def chmod_scripts(repo_root: Path) -> None:
    common = repo_root / "host" / "common"
    for name in ("install.sh", "start.sh", "stop.sh", "health.sh", "tunnel.sh"):
        path = common / name
        if path.is_file():
            path.chmod(path.stat().st_mode | 0o111)
