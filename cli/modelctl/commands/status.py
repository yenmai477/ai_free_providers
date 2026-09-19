"""modelctl status — show local state + optional live probe."""

from __future__ import annotations

import os

import requests

from modelctl.services.claude import resolve_api_key
from modelctl.services.state import load_state


def cmd_status(*, probe: bool = True) -> int:
    state = load_state()
    print(f"host:     {state.host or '(none)'}")
    print(f"model:    {state.model or '(none)'}")
    print(f"endpoint: {state.endpoint or '(none)'}")
    print(f"api_key_env: {state.api_key_env}")
    key = resolve_api_key(state)
    print(f"api_key:  {'set' if key else 'missing'} (from env)")

    if not probe or not state.endpoint:
        return 0

    url = state.endpoint.rstrip("/") + "/v1/models"
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        print(f"probe:    HTTP {resp.status_code} {url}")
        if resp.ok:
            data = resp.json()
            ids = [m.get("id") for m in data.get("data", [])]
            print(f"models:   {', '.join(ids) if ids else '(empty)'}")
        else:
            print(f"body:     {resp.text[:300]}")
            return 1
    except requests.RequestException as exc:
        print(f"probe:    FAILED — {exc}")
        return 1
    return 0
