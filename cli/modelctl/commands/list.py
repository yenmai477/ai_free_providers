"""modelctl models / hosts list commands."""

from __future__ import annotations

from pathlib import Path

from modelctl.services.registry import load_registry


def cmd_models(config_dir: Path | None = None) -> int:
    reg = load_registry(config_dir)
    print(f"{'ID':<20} {'OLLAMA':<18} {'MIN_VRAM':>8} {'MAX_CTX':>8}  CAPS")
    for mid, m in sorted(reg.models.items()):
        caps = ",".join(m.capabilities)
        print(
            f"{mid:<20} {m.model:<18} {m.min_vram_gb:>8.1f} {m.max_context:>8}  {caps}"
        )
    return 0


def cmd_hosts(config_dir: Path | None = None) -> int:
    reg = load_registry(config_dir)
    print(f"{'ID':<16} {'TYPE':<8} {'GPU':<6} {'VRAM':>5}  ALLOWED_MODELS")
    for hid, h in sorted(reg.hosts.items()):
        allowed = ",".join(h.allowed_models[:4])
        more = "" if len(h.allowed_models) <= 4 else f"+{len(h.allowed_models) - 4}"
        print(
            f"{hid:<16} {h.type:<8} {h.gpu_class:<6} {h.vram_gb:>5.0f}  {allowed}{more}"
        )
    return 0
