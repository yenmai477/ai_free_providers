"""modelctl endpoint / connect — manage public gateway URL."""

from __future__ import annotations

from urllib.parse import urlparse

from modelctl.services.claude import export_lines, print_exports
from modelctl.services.state import load_state, save_state


def _normalize_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return f"{parsed.scheme}://{parsed.netloc}"


def cmd_endpoint_get() -> int:
    state = load_state()
    if not state.endpoint:
        print("No endpoint set.")
        return 1
    print(state.endpoint)
    return 0


def cmd_endpoint_set(url: str, *, print_env: bool = True) -> int:
    state = load_state()
    state.endpoint = _normalize_url(url)
    save_state(state)
    print(f"Endpoint set: {state.endpoint}")
    if print_env:
        print()
        print_exports(state)
    return 0


def cmd_endpoint_env() -> int:
    state = load_state()
    try:
        print_exports(state)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    return 0


def cmd_connect(url: str) -> int:
    """Alias: set endpoint and print exports."""
    return cmd_endpoint_set(url, print_env=True)
