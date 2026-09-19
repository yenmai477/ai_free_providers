"""Colab bootstrap: path setup, installs, secrets."""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
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


def run_install_script(repo_root: Path) -> None:
    script = repo_root / "host" / "common" / "install.sh"
    subprocess.run(["bash", str(script)], check=True)


def chmod_scripts(repo_root: Path) -> None:
    common = repo_root / "host" / "common"
    for name in ("install.sh", "start.sh", "stop.sh", "health.sh", "tunnel.sh"):
        path = common / name
        if path.is_file():
            path.chmod(path.stat().st_mode | 0o111)
