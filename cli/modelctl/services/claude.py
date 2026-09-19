"""Claude Code / Anthropic-compatible client env helpers."""

from __future__ import annotations

import os
from pathlib import Path

from modelctl.services.state import State, load_state


def resolve_api_key(state: State | None = None) -> str | None:
    state = state or load_state()
    env_name = state.api_key_env or "GATEWAY_API_KEY"
    key = os.environ.get(env_name) or os.environ.get("ANTHROPIC_API_KEY")
    return key.strip() if key else None


def export_lines(state: State | None = None, *, api_key: str | None = None) -> list[str]:
    """Shell export lines for Anthropic-compatible clients."""
    state = state or load_state()
    if not state.endpoint:
        raise ValueError("No endpoint set. Run: modelctl endpoint set <url>")
    key = api_key if api_key is not None else resolve_api_key(state)
    lines = [
        f'export ANTHROPIC_BASE_URL="{state.endpoint.rstrip("/")}"',
    ]
    if key:
        lines.append(f'export ANTHROPIC_API_KEY="{key}"')
        lines.append(f'export {state.api_key_env}="{key}"')
    else:
        lines.append(
            f"# set {state.api_key_env} or ANTHROPIC_API_KEY in your environment"
        )
    return lines


def write_env_file(path: Path, state: State | None = None, *, api_key: str | None = None) -> Path:
    state = state or load_state()
    lines = export_lines(state, api_key=api_key)
    # Convert export FOO="bar" → FOO=bar for dotenv-style
    dotenv = []
    for line in lines:
        if line.startswith("#"):
            continue
        if line.startswith("export "):
            dotenv.append(line[len("export ") :])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(dotenv) + "\n", encoding="utf-8")
    return path


def print_exports(state: State | None = None) -> None:
    for line in export_lines(state):
        print(line)
