"""Load and validate models.yaml, hosts.yaml, and settings.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_DIR = REPO_ROOT / "config"


@dataclass(frozen=True)
class ModelConfig:
    id: str
    runtime: str
    model: str
    family: str
    size_gb: float
    min_vram_gb: float
    default_context: int
    max_context: int
    capabilities: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HostConfig:
    id: str
    type: str
    gpu_class: str
    vram_gb: float
    endpoint_mode: str
    allowed_models: list[str]
    gpu_profile: str | None = None


@dataclass(frozen=True)
class GpuProfile:
    id: str
    vram_gb: float
    reserved_vram_gb: float
    usable_vram_gb: float


@dataclass(frozen=True)
class Settings:
    ollama_port: int
    litellm_port: int
    api_key_env: str
    ollama_api_base: str
    gpu_profiles: dict[str, GpuProfile]
    paths: dict[str, str]


@dataclass(frozen=True)
class Registry:
    models: dict[str, ModelConfig]
    hosts: dict[str, HostConfig]
    settings: Settings
    config_dir: Path


def _require_keys(data: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise ValueError(f"{label} missing keys: {', '.join(missing)}")


def load_models(path: Path) -> dict[str, ModelConfig]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "models" not in raw:
        raise ValueError(f"Invalid models file: {path}")
    models: dict[str, ModelConfig] = {}
    for model_id, cfg in raw["models"].items():
        _require_keys(
            cfg,
            [
                "runtime",
                "model",
                "family",
                "size_gb",
                "min_vram_gb",
                "default_context",
                "max_context",
            ],
            f"model {model_id}",
        )
        models[model_id] = ModelConfig(
            id=model_id,
            runtime=cfg["runtime"],
            model=cfg["model"],
            family=cfg["family"],
            size_gb=float(cfg["size_gb"]),
            min_vram_gb=float(cfg["min_vram_gb"]),
            default_context=int(cfg["default_context"]),
            max_context=int(cfg["max_context"]),
            capabilities=list(cfg.get("capabilities", [])),
        )
    return models


def load_hosts(path: Path) -> dict[str, HostConfig]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "hosts" not in raw:
        raise ValueError(f"Invalid hosts file: {path}")
    hosts: dict[str, HostConfig] = {}
    for host_id, cfg in raw["hosts"].items():
        _require_keys(
            cfg,
            ["type", "gpu_class", "vram_gb", "endpoint_mode", "allowed_models"],
            f"host {host_id}",
        )
        hosts[host_id] = HostConfig(
            id=host_id,
            type=cfg["type"],
            gpu_class=cfg["gpu_class"],
            vram_gb=float(cfg["vram_gb"]),
            endpoint_mode=cfg["endpoint_mode"],
            allowed_models=list(cfg["allowed_models"]),
            gpu_profile=cfg.get("gpu_profile"),
        )
    return hosts


def load_settings(path: Path) -> Settings:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid settings file: {path}")
    ports = raw.get("ports", {})
    gateway = raw.get("gateway", {})
    profiles_raw = raw.get("gpu_profiles", {})
    profiles = {
        pid: GpuProfile(
            id=pid,
            vram_gb=float(p["vram_gb"]),
            reserved_vram_gb=float(p["reserved_vram_gb"]),
            usable_vram_gb=float(p["usable_vram_gb"]),
        )
        for pid, p in profiles_raw.items()
    }
    return Settings(
        ollama_port=int(ports.get("ollama", 11434)),
        litellm_port=int(ports.get("litellm", 4000)),
        api_key_env=str(gateway.get("api_key_env", "GATEWAY_API_KEY")),
        ollama_api_base=str(
            gateway.get("ollama_api_base", "http://127.0.0.1:11434/v1")
        ),
        gpu_profiles=profiles,
        paths=dict(raw.get("paths", {})),
    )


def load_registry(config_dir: Path | None = None) -> Registry:
    config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
    models = load_models(config_dir / "models.yaml")
    hosts = load_hosts(config_dir / "hosts.yaml")
    settings = load_settings(config_dir / "settings.yaml")

    for host in hosts.values():
        unknown = [m for m in host.allowed_models if m not in models]
        if unknown:
            raise ValueError(
                f"host {host.id} references unknown models: {', '.join(unknown)}"
            )
        if host.gpu_profile and host.gpu_profile not in settings.gpu_profiles:
            raise ValueError(
                f"host {host.id} references unknown gpu_profile: {host.gpu_profile}"
            )

    return Registry(
        models=models, hosts=hosts, settings=settings, config_dir=config_dir
    )


def get_usable_vram_gb(registry: Registry, host: HostConfig) -> float:
    if host.gpu_profile and host.gpu_profile in registry.settings.gpu_profiles:
        return registry.settings.gpu_profiles[host.gpu_profile].usable_vram_gb
    # Fallback: reserve 2 GB if no profile
    return max(0.0, host.vram_gb - 2.0)


def validate_selection(
    registry: Registry,
    host_id: str,
    model_id: str,
    context: int,
    *,
    available_vram_gb: float | None = None,
) -> tuple[HostConfig, ModelConfig]:
    """Validate host/model/context/(optional live VRAM). Raises ValueError."""
    if host_id not in registry.hosts:
        raise ValueError(f"Unknown host: {host_id}")
    if model_id not in registry.models:
        raise ValueError(f"Unknown model: {model_id}")

    host = registry.hosts[host_id]
    model = registry.models[model_id]

    if model_id not in host.allowed_models:
        raise ValueError(
            f"Model {model_id} is not allowed on host {host_id}. "
            f"Allowed: {', '.join(host.allowed_models)}"
        )

    usable = get_usable_vram_gb(registry, host)
    if model.min_vram_gb > usable:
        raise ValueError(
            f"{model_id} requires {model.min_vram_gb}GB usable VRAM; "
            f"host {host_id} has {usable}GB usable"
        )

    if available_vram_gb is not None and available_vram_gb < model.min_vram_gb:
        raise ValueError(
            f"{model_id} requires {model.min_vram_gb}GB; "
            f"detected available VRAM is {available_vram_gb}GB"
        )

    if context > model.max_context:
        raise ValueError(
            f"Context {context} exceeds max_context {model.max_context} for {model_id}"
        )
    if context < 1:
        raise ValueError("Context must be >= 1")

    return host, model
