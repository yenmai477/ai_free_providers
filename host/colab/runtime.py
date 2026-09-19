"""Colab runtime: validate → Ollama → LiteLLM → tunnel → READY."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Support both package import and flat Colab imports
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import bootstrap  # noqa: E402
from modelctl.services.gateway_config import write_litellm_config  # noqa: E402
from modelctl.services.health import (  # noqa: E402
    e2e_chat_completion,
    wait_for_gateway,
    wait_for_model,
    wait_for_ollama,
    wait_for_tunnel,
)
from modelctl.services.registry import load_registry, validate_selection  # noqa: E402
from modelctl.services.tunnel import wait_for_tunnel_url  # noqa: E402
from modelctl.services.vram import detect_gpus  # noqa: E402


@dataclass
class RuntimeResult:
    host_id: str
    model_id: str
    context: int
    gpu_name: str
    vram_gb: float
    endpoint: str
    api_key: str


def _banner(result: RuntimeResult) -> str:
    return f"""
╔═══════════════════════════════════════╗
║             MODEL READY               ║
╠═══════════════════════════════════════╣
║ Host       : {result.host_id:<26}║
║ GPU        : {result.gpu_name:<26}║
║ VRAM       : {f"{result.vram_gb:.1f} GB":<26}║
║ Model      : {result.model_id:<26}║
║ Context    : {str(result.context):<26}║
║ Runtime    : {"Ollama":<26}║
║ Gateway    : {"LiteLLM":<26}║
║                                       ║
║ Endpoint:                             ║
║ {result.endpoint:<37}║
║                                       ║
║ API key env: GATEWAY_API_KEY          ║
║ (printed once below — do not commit)  ║
╚═══════════════════════════════════════╝
""".rstrip()


def run(
    model_id: str = "qwen3-8b",
    context: int = 32768,
    host_id: str = "colab-t4-01",
    repo_root: Path | None = None,
    *,
    skip_install: bool = False,
    run_chat_probe: bool = True,
) -> RuntimeResult:
    root = Path(repo_root) if repo_root else bootstrap.find_repo_root()
    bootstrap.ensure_python_path(root)
    bootstrap.chmod_scripts(root)
    api_key = bootstrap.ensure_gateway_api_key()

    if not skip_install:
        bootstrap.run_install_script(root)

    registry = load_registry(root / "config")
    gpus = detect_gpus()
    gpu = gpus[0]
    available = gpu.memory_total_gb

    host, model = validate_selection(
        registry,
        host_id,
        model_id,
        context,
        available_vram_gb=available,
    )

    settings = registry.settings
    ollama_log = settings.paths.get("ollama_log", "/tmp/ollama.log")
    litellm_log = settings.paths.get("litellm_log", "/tmp/litellm.log")
    cloudflared_log = settings.paths.get("cloudflared_log", "/tmp/cloudflared.log")
    litellm_config = Path(
        settings.paths.get("litellm_config", "/tmp/litellm.yaml")
    )

    write_litellm_config(litellm_config, model_id, model, settings)

    bin_dir = str(Path.home() / ".local" / "bin")
    try:
        import sysconfig

        scripts_dir = sysconfig.get_path("scripts") or ""
    except Exception:  # noqa: BLE001
        scripts_dir = ""
    env = os.environ.copy()
    env["PATH"] = ":".join(
        p for p in [bin_dir, scripts_dir, "/usr/local/bin", env.get("PATH", "")] if p
    )
    # Colab GPU: Ollama needs system NVIDIA libs
    nvidia = "/usr/lib64-nvidia"
    if Path(nvidia).is_dir():
        ld = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = f"{nvidia}:{ld}" if ld else nvidia
    env.update(
        {
            "OLLAMA_MODEL": model.model,
            "GATEWAY_API_KEY": api_key,
            "LITELLM_CONFIG": str(litellm_config),
            "LITELLM_PORT": str(settings.litellm_port),
            "OLLAMA_LOG": ollama_log,
            "LITELLM_LOG": litellm_log,
            "CLOUDFLARED_LOG": cloudflared_log,
            "MODEL_ID": model_id,
            "OLLAMA_NUM_CTX": str(context),
            "PYTHON_BIN": sys.executable,
            "BIN_DIR": bin_dir,
            "LITELLM_MASTER_KEY": api_key,
            "CONFIG_FILE_PATH": str(litellm_config),
        }
    )

    common = root / "host" / "common"

    def _dump_host_logs() -> None:
        for label, path in (
            ("litellm", litellm_log),
            ("ollama", ollama_log),
            ("cloudflared", cloudflared_log),
        ):
            p = Path(path)
            print(f"======== {label} log: {p} ========")
            if p.exists():
                print(p.read_text(encoding="utf-8", errors="replace")[-5000:])
            else:
                print("(missing)")

    def _run_script(path: Path, *, check: bool) -> None:
        result = subprocess.run(["bash", str(path)], env=env)
        if result.returncode != 0 and check:
            _dump_host_logs()
            raise RuntimeError(
                f"{path.name} failed (exit {result.returncode}). "
                "See log dumps above."
            )

    _run_script(common / "stop.sh", check=False)
    time.sleep(1)
    _run_script(common / "start.sh", check=True)

    print("[runtime] waiting for Ollama…")
    wait_for_ollama()
    print("[runtime] waiting for model…")
    wait_for_model(model.model)
    print("[runtime] waiting for LiteLLM…")
    try:
        wait_for_gateway(
            base=f"http://127.0.0.1:{settings.litellm_port}", api_key=api_key
        )
    except TimeoutError:
        log_path = Path(litellm_log)
        print("[runtime] LiteLLM failed to become ready. Last log lines:")
        if log_path.exists():
            print(log_path.read_text(encoding="utf-8", errors="replace")[-4000:])
        else:
            print(f"(no log at {log_path})")
        raise


    _run_script(common / "tunnel.sh", check=True)
    print("[runtime] waiting for Cloudflare URL…")
    public_url = wait_for_tunnel_url(Path(cloudflared_log), timeout_s=90.0)

    print("[runtime] public /v1/models…")
    wait_for_tunnel(public_url, api_key)

    checks = [
        "✅ Ollama",
        "✅ Model",
        "✅ LiteLLM",
        "✅ Cloudflare",
        "✅ Public API",
    ]
    if run_chat_probe:
        print("[runtime] e2e chat completion…")
        e2e_chat_completion(public_url, api_key, model_id)
        checks.append("✅ Chat completion")

    result = RuntimeResult(
        host_id=host.id,
        model_id=model_id,
        context=context,
        gpu_name=gpu.name,
        vram_gb=available,
        endpoint=public_url,
        api_key=api_key,
    )
    print(_banner(result))
    for line in checks:
        print(line)
    print(f"\nGATEWAY_API_KEY={api_key}")
    print(f"export ANTHROPIC_BASE_URL={public_url}")
    print(f"export ANTHROPIC_API_KEY={api_key}")
    return result
