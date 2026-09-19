"""Health checks for Ollama, LiteLLM, and public tunnel endpoint."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import requests


def wait_for_http(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout_s: float = 120.0,
    interval_s: float = 2.0,
    expect_status: int = 200,
) -> requests.Response:
    deadline = time.time() + timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == expect_status:
                return resp
            last_error = RuntimeError(f"{url} returned {resp.status_code}")
        except Exception as exc:  # noqa: BLE001 — retry until timeout
            last_error = exc
        time.sleep(interval_s)
    raise TimeoutError(f"Timed out waiting for {url}: {last_error}")


def wait_for_ollama(
    base: str = "http://127.0.0.1:11434", timeout_s: float = 120.0
) -> dict[str, Any]:
    resp = wait_for_http(f"{base}/api/tags", timeout_s=timeout_s)
    return resp.json()


def wait_for_model(
    ollama_model: str,
    base: str = "http://127.0.0.1:11434",
    timeout_s: float = 300.0,
) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        data = wait_for_ollama(base=base, timeout_s=min(30.0, timeout_s))
        names = {m.get("name") for m in data.get("models", [])}
        # Ollama may report "qwen3:8b" or "qwen3:8b:latest"
        if ollama_model in names or f"{ollama_model}:latest" in names:
            return
        # Also accept prefix match
        if any(n.startswith(ollama_model) for n in names if n):
            return
        time.sleep(2)
    raise TimeoutError(f"Model {ollama_model} not available in Ollama")


def wait_for_gateway(
    base: str = "http://127.0.0.1:4000",
    api_key: str = "",
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    # LiteLLM exposes /health and /v1/models
    try:
        wait_for_http(f"{base}/health", timeout_s=min(30.0, timeout_s))
    except TimeoutError:
        pass
    resp = wait_for_http(
        f"{base}/v1/models", headers=headers, timeout_s=timeout_s
    )
    return resp.json()


def wait_for_tunnel(
    public_url: str,
    api_key: str,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}"}
    url = urljoin(public_url.rstrip("/") + "/", "v1/models")
    resp = wait_for_http(url, headers=headers, timeout_s=timeout_s)
    return resp.json()


def e2e_chat_completion(
    base_url: str,
    api_key: str,
    model_id: str,
    *,
    timeout_s: float = 180.0,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
        "max_tokens": 16,
    }
    url = urljoin(base_url.rstrip("/") + "/", "v1/chat/completions")
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    resp.raise_for_status()
    return resp.json()
