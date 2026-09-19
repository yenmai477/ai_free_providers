"""Generate single-model LiteLLM config from registry selection."""

from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from modelctl.services.registry import ModelConfig, Settings

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEMPLATE_DIR = REPO_ROOT / "gateway" / "templates"


def render_litellm_yaml(
    model_id: str,
    model: ModelConfig,
    settings: Settings,
    *,
    template_dir: Path | None = None,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_dir or DEFAULT_TEMPLATE_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template("litellm.yaml.j2")
    return template.render(
        model_id=model_id,
        ollama_model=model.model,
        api_base=settings.ollama_api_base,
    )


def write_litellm_config(
    path: Path,
    model_id: str,
    model: ModelConfig,
    settings: Settings,
    *,
    template_dir: Path | None = None,
) -> Path:
    content = render_litellm_yaml(
        model_id, model, settings, template_dir=template_dir
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def litellm_config_dict(
    model_id: str, model: ModelConfig, settings: Settings
) -> dict:
    """Programmatic equivalent used by tests / runtime without Jinja."""
    return {
        "model_list": [
            {
                "model_name": model_id,
                "litellm_params": {
                    "model": f"ollama_chat/{model.model}",
                    "api_base": "http://127.0.0.1:11434",
                    "api_key": "ollama",
                    "think": False,
                },
            }
        ],
        "general_settings": {
            "master_key": "os.environ/LITELLM_MASTER_KEY",
        },
    }


def assert_single_model_config(yaml_text: str) -> str:
    data = yaml.safe_load(yaml_text)
    models = data.get("model_list") or []
    if len(models) != 1:
        raise ValueError(f"Expected exactly one model in LiteLLM config, got {len(models)}")
    return models[0]["model_name"]
