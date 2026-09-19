"""VRAM parsing and gating tests."""

from __future__ import annotations

import pytest

from modelctl.services.vram import (
    available_vram_gb,
    detect_gpus,
    parse_nvidia_smi_csv,
)


def test_parse_nvidia_smi_csv():
    raw = "Tesla T4, 15360 MiB\n"
    gpus = parse_nvidia_smi_csv(raw)
    assert len(gpus) == 1
    assert gpus[0].name == "Tesla T4"
    assert abs(gpus[0].memory_total_gb - 15.0) < 0.01


def test_parse_multiple_gpus():
    raw = "GPU A, 8192 MiB\nGPU B, 16384 MiB\n"
    gpus = parse_nvidia_smi_csv(raw)
    assert available_vram_gb(gpus) == pytest.approx(24.0)


def test_detect_gpus_injectable_runner():
    def fake_runner(cmd: list[str]) -> str:
        assert "nvidia-smi" in cmd[0]
        return "Tesla T4, 15109 MiB\n"

    gpus = detect_gpus(runner=fake_runner)
    assert gpus[0].name == "Tesla T4"


def test_empty_output_errors():
    with pytest.raises(ValueError, match="No GPUs"):
        parse_nvidia_smi_csv("\n")
