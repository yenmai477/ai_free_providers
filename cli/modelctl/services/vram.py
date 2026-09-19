"""GPU / VRAM detection helpers."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class GpuInfo:
    name: str
    memory_total_mib: float

    @property
    def memory_total_gb(self) -> float:
        return self.memory_total_mib / 1024.0


def parse_nvidia_smi_csv(output: str) -> list[GpuInfo]:
    """Parse `nvidia-smi --query-gpu=name,memory.total --format=csv,noheader`."""
    gpus: list[GpuInfo] = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Example: "Tesla T4, 15360 MiB"
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            raise ValueError(f"Unexpected nvidia-smi line: {line!r}")
        name = parts[0]
        mem_match = re.search(r"([\d.]+)", parts[1])
        if not mem_match:
            raise ValueError(f"Could not parse memory from: {line!r}")
        gpus.append(GpuInfo(name=name, memory_total_mib=float(mem_match.group(1))))
    if not gpus:
        raise ValueError("No GPUs found in nvidia-smi output")
    return gpus


def detect_gpus(
    runner: Callable[[list[str]], str] | None = None,
) -> list[GpuInfo]:
    """Run nvidia-smi and return GPU info. `runner` is injectable for tests."""

    def default_runner(cmd: list[str]) -> str:
        return subprocess.check_output(cmd, text=True)

    run = runner or default_runner
    output = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total",
            "--format=csv,noheader",
        ]
    )
    return parse_nvidia_smi_csv(output)


def available_vram_gb(gpus: list[GpuInfo] | None = None) -> float:
    """Total VRAM across GPUs (Phase 1 assumes single GPU)."""
    if gpus is None:
        gpus = detect_gpus()
    return sum(g.memory_total_gb for g in gpus)
