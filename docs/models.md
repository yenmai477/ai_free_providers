# Models

Definitions live in `config/models.yaml`. Host allow-lists live in `config/hosts.yaml`.

## Registry (Ollama tags)

| ID | Ollama | min VRAM | default ctx | max ctx | Notes |
|----|--------|----------|-------------|---------|-------|
| qwen3-4b | qwen3:4b | 5 | 32k | 65k | Small / fast |
| gemma3-4b | gemma3:4b | 5 | 32k | 65k | Vision |
| mistral-7b | mistral:7b | 7 | 32k | 32k | General |
| llama3-8b | llama3.1:8b | 8 | 32k | 32k | Coding |
| qwen3-8b | qwen3:8b | 8 | 32k | 32k | Default coding |
| deepseek-r1-8b | deepseek-r1:8b | 8 | 16k | 32k | Reasoning |
| gemma3-12b | gemma3:12b | 11 | 16k | 32k | Tight on T4 |
| deepseek-r1-14b | deepseek-r1:14b | 12 | 8k | 16k | Use low ctx on T4 |
| qwen3-14b | qwen3:14b | 12 | 16k | 16k | Better agent; low ctx |

T4 usable budget ≈ **13 GB** (`gpu_profiles.t4-16gb`). Sizes are quantized baselines, not guarantees.

## Switching models

1. Colab **Runtime → Restart session**
2. Pick `MODEL` + safe `CONTEXT` in the notebook
3. Run all → `modelctl connect` + `modelctl use <host> <model>` on PC

Still **one model per session** (VRAM).
