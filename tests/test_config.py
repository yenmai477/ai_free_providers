"""Config / settings consistency tests."""

from __future__ import annotations

from pathlib import Path

from modelctl.services.registry import get_usable_vram_gb, load_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"


def test_t4_usable_vram_budget():
    reg = load_registry(CONFIG_DIR)
    host = reg.hosts["colab-t4-01"]
    usable = get_usable_vram_gb(reg, host)
    assert usable == 13.0
    # Phase 1 model fits
    assert reg.models["qwen3-8b"].min_vram_gb <= usable


def test_all_allowed_models_exist():
    reg = load_registry(CONFIG_DIR)
    for host in reg.hosts.values():
        for mid in host.allowed_models:
            assert mid in reg.models


def test_tunnel_url_parser():
    from modelctl.services.tunnel import parse_tunnel_url

    log = "INF | https://abc-123.trycloudflare.com |\n"
    assert parse_tunnel_url(log) == "https://abc-123.trycloudflare.com"
    assert parse_tunnel_url("no url here") is None
