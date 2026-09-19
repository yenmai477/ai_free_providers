"""Model/host selection and LiteLLM single-model config."""

from __future__ import annotations

from pathlib import Path

from modelctl.services.gateway_config import (
    assert_single_model_config,
    litellm_config_dict,
    render_litellm_yaml,
)
from modelctl.services.registry import load_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"


def test_phase1_qwen_selection_renders_single_model():
    reg = load_registry(CONFIG_DIR)
    model = reg.models["qwen3-8b"]
    yaml_text = render_litellm_yaml("qwen3-8b", model, reg.settings)
    name = assert_single_model_config(yaml_text)
    assert name == "qwen3-8b"
    assert "ollama_chat/qwen3:8b" in yaml_text
    assert "think: false" in yaml_text
    assert "11434" in yaml_text


def test_litellm_config_dict_single_entry():
    reg = load_registry(CONFIG_DIR)
    model = reg.models["qwen3-8b"]
    cfg = litellm_config_dict("qwen3-8b", model, reg.settings)
    assert len(cfg["model_list"]) == 1
    params = cfg["model_list"][0]["litellm_params"]
    assert params["model"] == "ollama_chat/qwen3:8b"
    assert params["think"] is False
