"""Registry loading and selection validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelctl.services.registry import (
    load_registry,
    validate_selection,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"


def test_load_registry_models_and_hosts():
    reg = load_registry(CONFIG_DIR)
    assert "qwen3-8b" in reg.models
    assert reg.models["qwen3-8b"].model == "qwen3:8b"
    assert "colab-t4-01" in reg.hosts
    assert "qwen3-8b" in reg.hosts["colab-t4-01"].allowed_models
    assert reg.settings.litellm_port == 4000
    assert "t4-16gb" in reg.settings.gpu_profiles
    assert reg.settings.gpu_profiles["t4-16gb"].usable_vram_gb == 13


def test_validate_selection_ok():
    reg = load_registry(CONFIG_DIR)
    host, model = validate_selection(
        reg, "colab-t4-01", "qwen3-8b", 32768, available_vram_gb=15.0
    )
    assert host.id == "colab-t4-01"
    assert model.id == "qwen3-8b"


def test_model_not_allowed_on_host():
    reg = load_registry(CONFIG_DIR)
    with pytest.raises(ValueError, match="not allowed"):
        validate_selection(reg, "colab-t4-02", "mistral-7b", 8192)


def test_context_too_large():
    reg = load_registry(CONFIG_DIR)
    with pytest.raises(ValueError, match="exceeds max_context"):
        validate_selection(reg, "colab-t4-01", "qwen3-8b", 999999)


def test_vram_gate_detected():
    reg = load_registry(CONFIG_DIR)
    with pytest.raises(ValueError, match="detected available VRAM"):
        validate_selection(
            reg, "colab-t4-01", "qwen3-8b", 8192, available_vram_gb=4.0
        )


def test_unknown_model():
    reg = load_registry(CONFIG_DIR)
    with pytest.raises(ValueError, match="Unknown model"):
        validate_selection(reg, "colab-t4-01", "nope", 4096)
