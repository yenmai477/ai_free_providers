"""Local modelctl state under ~/.modelctl/."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def default_home() -> Path:
    override = os.environ.get("MODELCTL_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".modelctl"


@dataclass
class State:
    host: str | None = None
    model: str | None = None
    endpoint: str | None = None
    api_key_env: str = "GATEWAY_API_KEY"
    # Optional cached key name only — never persist secrets by default
    notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> State:
        return cls(
            host=data.get("host"),
            model=data.get("model"),
            endpoint=data.get("endpoint"),
            api_key_env=data.get("api_key_env") or "GATEWAY_API_KEY",
            notes=dict(data.get("notes") or {}),
        )


def ensure_dirs(home: Path | None = None) -> Path:
    root = home or default_home()
    root.mkdir(parents=True, exist_ok=True)
    return root


def state_path(home: Path | None = None) -> Path:
    return ensure_dirs(home) / "state.json"


def load_state(home: Path | None = None) -> State:
    path = state_path(home)
    if not path.is_file():
        return State()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid state file: {path}")
    return State.from_dict(data)


def save_state(state: State, home: Path | None = None) -> Path:
    path = state_path(home)
    ensure_dirs(home)
    path.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def clear_endpoint(home: Path | None = None) -> State:
    state = load_state(home)
    state.endpoint = None
    save_state(state, home)
    return state
