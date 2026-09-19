"""Claude Code / Anthropic-compatible client env helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path

from modelctl.services.state import State, load_state


def resolve_api_key(state: State | None = None) -> str | None:
    state = state or load_state()
    env_name = state.api_key_env or "GATEWAY_API_KEY"
    key = (
        os.environ.get(env_name)
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or os.environ.get("ANTHROPIC_API_KEY")
    )
    return key.strip() if key else None


def claude_env_dict(
    state: State | None = None, *, api_key: str | None = None
) -> dict[str, str]:
    """Env map for Claude Code (shell or settings.json)."""
    state = state or load_state()
    if not state.endpoint:
        raise ValueError("No endpoint set. Run: modelctl endpoint set <url>")
    key = api_key if api_key is not None else resolve_api_key(state)
    if not key:
        raise ValueError(
            f"Set {state.api_key_env} (or ANTHROPIC_AUTH_TOKEN) in your environment"
        )
    model = state.model or "qwen3-8b"
    # Prefer plain registry id (always on /v1/models). *-claude aliases need Colab rebuild.
    return {
        "ANTHROPIC_BASE_URL": state.endpoint.rstrip("/"),
        "ANTHROPIC_AUTH_TOKEN": key,
        "ANTHROPIC_API_KEY": key,
        state.api_key_env: key,
        "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
        "ANTHROPIC_MODEL": model,
        "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
        "CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT": "1",
    }


def export_lines(state: State | None = None, *, api_key: str | None = None) -> list[str]:
    """Shell export lines for Anthropic-compatible clients."""
    env = claude_env_dict(state, api_key=api_key)
    return [f'export {k}="{v}"' for k, v in env.items()]


def write_env_file(
    path: Path, state: State | None = None, *, api_key: str | None = None
) -> Path:
    env = claude_env_dict(state, api_key=api_key)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(f"{k}={v}" for k, v in env.items()) + "\n", encoding="utf-8"
    )
    return path


def default_claude_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def write_claude_settings(
    path: Path | None = None,
    state: State | None = None,
    *,
    api_key: str | None = None,
    merge: bool = True,
) -> Path:
    """Write/merge env block into ~/.claude/settings.json for Claude Code."""
    path = path or default_claude_settings_path()
    env = claude_env_dict(state, api_key=api_key)
    data: dict = {}
    if merge and path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = raw
        except json.JSONDecodeError:
            data = {}
    existing_env = data.get("env") if isinstance(data.get("env"), dict) else {}
    data["env"] = {**existing_env, **env}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def print_exports(state: State | None = None) -> None:
    for line in export_lines(state):
        print(line)
