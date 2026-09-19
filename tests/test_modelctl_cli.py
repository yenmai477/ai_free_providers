"""modelctl state + CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

from modelctl.commands.endpoint import cmd_connect, cmd_endpoint_get
from modelctl.commands.use import cmd_use
from modelctl.main import main
from modelctl.services.state import load_state


def test_cli_models_hosts(capsys):
    assert main(["models"]) == 0
    out = capsys.readouterr().out
    assert "qwen3-8b" in out
    assert main(["hosts"]) == 0
    out = capsys.readouterr().out
    assert "colab-t4-01" in out


def test_use_and_endpoint(tmp_path: Path, monkeypatch, config_dir=None):
    monkeypatch.setenv("MODELCTL_HOME", str(tmp_path))
    from modelctl.services.registry import DEFAULT_CONFIG_DIR

    assert cmd_use("colab-t4-01", "qwen3-8b", config_dir=DEFAULT_CONFIG_DIR) == 0
    state = load_state()
    assert state.host == "colab-t4-01"
    assert state.model == "qwen3-8b"

    assert cmd_connect("https://demo.trycloudflare.com") == 0
    assert load_state().endpoint == "https://demo.trycloudflare.com"
    assert cmd_endpoint_get() == 0
