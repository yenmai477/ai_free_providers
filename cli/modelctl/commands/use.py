"""modelctl use — bind local selection (host + model)."""

from __future__ import annotations

from pathlib import Path

from modelctl.services.registry import load_registry, validate_selection
from modelctl.services.state import load_state, save_state


def cmd_use(
    host_id: str,
    model_id: str,
    *,
    context: int | None = None,
    config_dir: Path | None = None,
) -> int:
    reg = load_registry(config_dir)
    model = reg.models.get(model_id)
    ctx = context if context is not None else (model.default_context if model else 4096)
    validate_selection(reg, host_id, model_id, ctx)

    state = load_state()
    state.host = host_id
    state.model = model_id
    save_state(state)
    print(f"Selected host={host_id} model={model_id}")
    if state.endpoint:
        print(f"Endpoint unchanged: {state.endpoint}")
    else:
        print("No endpoint yet. After Colab READY: modelctl endpoint set <url>")
    return 0
