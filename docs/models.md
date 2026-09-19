# Models

Definitions live in `config/models.yaml`. Host allow-lists live in `config/hosts.yaml`.

Phase 1 runtime uses **qwen3-8b** only (`ollama` tag `qwen3:8b`).

VRAM numbers are baseline quantized sizes, not guarantees. T4 usable budget is ~13 GB after reserved overhead (`config/settings.yaml` → `gpu_profiles.t4-16gb`).
