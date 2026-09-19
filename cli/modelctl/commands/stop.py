"""modelctl stop — clear local endpoint binding (does not stop Colab)."""

from __future__ import annotations

from modelctl.services.state import clear_endpoint, load_state, save_state


def cmd_stop(*, clear_selection: bool = False) -> int:
    state = load_state()
    if clear_selection:
        state.host = None
        state.model = None
        state.endpoint = None
        save_state(state)
        print("Cleared host, model, and endpoint from local state.")
    else:
        clear_endpoint()
        print("Cleared endpoint from local state (host/model kept).")
        print("Colab runtime is NOT stopped — stop it in the notebook if needed.")
    return 0
