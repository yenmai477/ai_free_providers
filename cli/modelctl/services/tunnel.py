"""Cloudflare quick tunnel helpers."""

from __future__ import annotations

import re
import time
from pathlib import Path

TUNNEL_URL_PATTERN = re.compile(
    r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com"
)


def parse_tunnel_url(log_text: str) -> str | None:
    match = TUNNEL_URL_PATTERN.search(log_text)
    return match.group(0) if match else None


def wait_for_tunnel_url(
    log_path: Path,
    *,
    timeout_s: float = 60.0,
    interval_s: float = 1.0,
) -> str:
    deadline = time.time() + timeout_s
    log_path = Path(log_path)
    while time.time() < deadline:
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            url = parse_tunnel_url(text)
            if url:
                return url
        time.sleep(interval_s)
    raise TimeoutError(
        f"No trycloudflare URL found in {log_path} within {timeout_s}s"
    )
