"""modelctl claude — configure Claude Code for the gateway."""

from __future__ import annotations

from pathlib import Path

from modelctl.services.claude import (
    default_claude_settings_path,
    print_exports,
    write_claude_settings,
)
from modelctl.services.state import load_state


def cmd_claude_env() -> int:
    try:
        print_exports()
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    return 0


def cmd_claude_setup(*, settings_path: Path | None = None) -> int:
    state = load_state()
    try:
        path = write_claude_settings(settings_path, state)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    print(f"Wrote Claude Code settings: {path}")
    print()
    print("Next:")
    print("  1. Ensure Colab gateway is READY (modelctl status)")
    print("  2. Open a NEW terminal")
    print("  3. cd into the repo, then:  claude")
    print("     Example:  cd D:\\MY_CODE\\ai_free_providers; claude")
    print("  4. Accept workspace trust when prompted")
    print("  5. Ask: Read README.md and summarize the repo")
    print("     (must use Read/Glob tools — if model says it cannot access files,")
    print("      Qwen tool-calling via gateway is failing; try a larger model)")
    print()
    print("Verify Anthropic Messages API:")
    ep = state.endpoint.rstrip("/") if state.endpoint else "https://YOUR_TUNNEL"
    print(
        f'  curl -sS "{ep}/v1/messages" -H "Authorization: Bearer $env:GATEWAY_API_KEY" '
        '-H "Content-Type: application/json" '
        '-H "anthropic-version: 2023-06-01" '
        '-d "{{\\"model\\":\\"qwen3-8b\\",\\"max_tokens\\":64,'
        '\\"messages\\":[{{\\"role\\":\\"user\\",\\"content\\":\\"hi\\"}}]}}"'
    )
    print()
    print(f"(default path: {default_claude_settings_path()})")
    return 0
