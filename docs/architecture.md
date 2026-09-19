Được. Nếu bạn **work chủ yếu bằng Cursor**, mình sẽ thiết kế project này như một repo thật, để Cursor có thể hiểu architecture và implement từng phase mà không bị "AI spaghetti".

Mục tiêu cuối:

```
┌─────────────────────────────────────────────────────────────┐
│                         YOUR PC                             │
│                                                             │
│  Cursor / Claude Code                                       │
│          │                                                  │
│          │ Anthropic-compatible API                         │
│          ▼                                                  │
│  ┌───────────────────────┐                                  │
│  │ local CLI / config    │                                  │
│  │ modelctl              │                                  │
│  └───────────┬───────────┘                                  │
└──────────────┼──────────────────────────────────────────────┘
               │
               │ HTTPS
               ▼
       Cloudflare Quick Tunnel
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    ACTIVE FREE HOST                          │
│                 Google Colab / HF                            │
│                                                              │
│  ┌──────────────┐                                            │
│  │ cloudflared  │                                            │
│  └──────┬───────┘                                            │
│         ▼                                                    │
│  ┌──────────────┐                                            │
│  │ LiteLLM      │ :4000                                     │
│  │ Adapter      │                                            │
│  └──────┬───────┘                                            │
│         ▼                                                    │
│  ┌──────────────┐                                            │
│  │ Ollama       │ :11434                                   │
│  └──────┬───────┘                                            │
│         ▼                                                    │
│  ┌──────────────────────┐                                    │
│  │ EXACTLY ONE MODEL    │                                    │
│  │                      │                                    │
│  │ qwen3:8b             │                                    │
│  │ OR qwen3:14b         │                                    │
│  │ OR llama3.1:8b       │                                    │
│  └──────────────────────┘                                    │
└──────────────────────────────────────────────────────────────┘

```

## 1. Nguyên tắc architecture

Mình sẽ giữ 5 nguyên tắc:

1. **Một host chỉ chạy một model.**
2. **Model registry độc lập với host registry.**
3. **Claude Code/Cursor không biết host thật ở đâu.**
4. **Cloudflare URL có thể thay đổi;** `modelctl` **tự cập nhật.**
5. **Host chết không làm hỏng config của client.**

Có một lưu ý: nếu bạn muốn **Claude Code dùng Anthropic API semantics**, LiteLLM sẽ đóng vai trò adapter/router; Ollama chỉ là model runtime.

---

# 2. Repository

Mình đề xuất repo:

```
free-model-gateway/
│
├── README.md
├── AGENTS.md
├── Makefile
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── config/
│   ├── models.yaml
│   ├── hosts.yaml
│   └── settings.yaml
│
├── cli/
│   └── modelctl/
│       ├── __init__.py
│       ├── main.py
│       ├── commands/
│       │   ├── list.py
│       │   ├── use.py
│       │   ├── status.py
│       │   └── stop.py
│       ├── adapters/
│       │   ├── colab.py
│       │   ├── huggingface.py
│       │   └── local.py
│       └── services/
│           ├── registry.py
│           ├── health.py
│           ├── tunnel.py
│           └── claude.py
│
├── gateway/
│   ├── litellm.yaml
│   └── templates/
│       └── litellm.yaml.j2
│
├── host/
│   ├── common/
│   │   ├── install.sh
│   │   ├── start.sh
│   │   ├── stop.sh
│   │   ├── health.sh
│   │   └── tunnel.sh
│   │
│   └── colab/
│       ├── notebook.ipynb
│       ├── bootstrap.py
│       └── runtime.py
│
├── tests/
│   ├── test_registry.py
│   ├── test_model_selection.py
│   ├── test_vram.py
│   └── test_config.py
│
└── docs/
    ├── architecture.md
    ├── colab.md
    ├── models.md
    └── troubleshooting.md

```

Đây là structure Cursor rất dễ navigate.

---

# 3. Model registry

`config/models.yaml`:

```
version: 1

models:

  qwen3-4b:
    runtime: ollama
    model: qwen3:4b
    family: qwen
    size_gb: 2.5
    min_vram_gb: 5
    default_context: 32768
    max_context: 65536
    capabilities:
      - coding
      - general

  gemma3-4b:
    runtime: ollama
    model: gemma3:4b
    family: gemma
    size_gb: 3.3
    min_vram_gb: 5
    default_context: 32768
    max_context: 65536
    capabilities:
      - general
      - vision

  mistral-7b:
    runtime: ollama
    model: mistral:7b
    family: mistral
    size_gb: 4.4
    min_vram_gb: 7
    default_context: 32768
    max_context: 32768
    capabilities:
      - general
      - coding

  llama3-8b:
    runtime: ollama
    model: llama3.1:8b
    family: llama
    size_gb: 4.9
    min_vram_gb: 8
    default_context: 32768
    max_context: 32768
    capabilities:
      - general
      - coding

  qwen3-8b:
    runtime: ollama
    model: qwen3:8b
    family: qwen
    size_gb: 5.2
    min_vram_gb: 8
    default_context: 32768
    max_context: 32768
    capabilities:
      - coding
      - general

  deepseek-r1-8b:
    runtime: ollama
    model: deepseek-r1:8b
    family: deepseek
    size_gb: 5.2
    min_vram_gb: 8
    default_context: 16384
    max_context: 32768
    capabilities:
      - reasoning
      - coding

  gemma3-12b:
    runtime: ollama
    model: gemma3:12b
    family: gemma
    size_gb: 8.1
    min_vram_gb: 11
    default_context: 16384
    max_context: 32768
    capabilities:
      - general
      - vision

  deepseek-r1-14b:
    runtime: ollama
    model: deepseek-r1:14b
    family: deepseek
    size_gb: 9.0
    min_vram_gb: 12
    default_context: 8192
    max_context: 16384
    capabilities:
      - reasoning
      - coding

  qwen3-14b:
    runtime: ollama
    model: qwen3:14b
    family: qwen
    size_gb: 9.3
    min_vram_gb: 12
    default_context: 16384
    max_context: 16384
    capabilities:
      - coding
      - reasoning
      - general

```

Các size ở đây là **baseline cho quantized Ollama artifacts theo danh sách bạn đưa**, không phải VRAM guarantee.

---

# 4. Host registry

`config/hosts.yaml`:

```
version: 1

hosts:

  colab-t4-01:
    type: colab
    gpu_class: t4
    vram_gb: 15
    endpoint_mode: quick_tunnel

    allowed_models:
      - qwen3-4b
      - gemma3-4b
      - mistral-7b
      - llama3-8b
      - qwen3-8b
      - deepseek-r1-8b
      - gemma3-12b
      - deepseek-r1-14b
      - qwen3-14b

  colab-t4-02:
    type: colab
    gpu_class: t4
    vram_gb: 15
    endpoint_mode: quick_tunnel

    allowed_models:
      - qwen3-4b
      - gemma3-4b
      - llama3-8b
      - qwen3-8b
      - qwen3-14b

```

Điểm quan trọng:

```
models.yaml
    =
model capabilities

hosts.yaml
    =
host capabilities

```

Sau này có A100:

```
colab-a100:
  gpu_class: a100
  vram_gb: 40

```

không phải sửa model definition.

---

# 5. Colab Notebook

Notebook chỉ có **một input quan trọng**:

```
MODEL = "qwen3-8b" # @param [
# "qwen3-4b",
# "gemma3-4b",
# "mistral-7b",
# "llama3-8b",
# "qwen3-8b",
# "deepseek-r1-8b",
# "gemma3-12b",
# "deepseek-r1-14b",
# "qwen3-14b"
# ]

```

Thêm:

```
CONTEXT = 32768 # @param [4096, 8192, 16384, 32768, 65536]

```

và:

```
HOST_ID = "colab-t4-01"

```

---

# 6. Notebook flow

### Cell 1 — Configuration

```
MODEL = "qwen3-8b"
CONTEXT = 32768
HOST_ID = "colab-t4-01"

```

### Cell 2 — Detect GPU

```
import subprocess

result = subprocess.check_output(
    [
        "nvidia-smi",
        "--query-gpu=name,memory.total",
        "--format=csv,noheader"
    ],
    text=True
)

print(result)

```

### Cell 3 — Load registry

```
import yaml

with open("models.yaml") as f:
    models = yaml.safe_load(f)["models"]

config = models[MODEL]

```

### Cell 4 — Validate

```
available_vram_gb = ...

if available_vram_gb < config["min_vram_gb"]:
    raise RuntimeError(
        f"{MODEL} requires {config['min_vram_gb']}GB"
    )

if CONTEXT > config["max_context"]:
    raise RuntimeError(
        f"Context too large for {MODEL}"
    )

```

### Cell 5 — Install Ollama

```
curl -fsSL https://ollama.com/install.sh | sh

```

### Cell 6 — Start Ollama

```
ollama serve > /tmp/ollama.log 2>&1 &

```

### Cell 7 — Pull ONLY selected model

```
subprocess.run([
    "ollama",
    "pull",
    config["model"]
], check=True)

```

### Cell 8 — Start model

Ollama sẽ load model on demand:

```
ollama run qwen3:8b

```

hoặc để API phục vụ model.

---

# 7. Quan trọng: Ollama model lifecycle

Bạn muốn **chỉ một model trong VRAM**.

Vậy phải explicit unload model cũ.

Ví dụ:

```
ollama stop qwen3:8b

```

trước khi start model mới.

Nhưng vì architecture là:

> **mỗi notebook session chỉ chọn 1 model**

thì thậm chí không cần runtime switching.

Đây là ưu điểm rất lớn.

```
Run notebook
    ↓
select Qwen
    ↓
Qwen loaded
    ↓
session ends

```

Muốn GLM:

```
restart runtime
    ↓
select GLM
    ↓
GLM loaded

```

Không có trạng thái phức tạp.

---

# 8. LiteLLM adapter

`gateway/litellm.yaml` được generate:

```
model_list:

  - model_name: qwen3-8b
    litellm_params:
      model: openai/qwen3:8b
      api_base: http://127.0.0.1:11434/v1
      api_key: ollama

general_settings:
  master_key: ${GATEWAY_API_KEY}

```

Nhưng tốt hơn là **generate file này từ selected model**.

Ví dụ Python:

```
selected = models[MODEL]

litellm_config = {
    "model_list": [
        {
            "model_name": MODEL,
            "litellm_params": {
                "model": f"openai/{selected['model']}",
                "api_base": "http://127.0.0.1:11434/v1",
                "api_key": "ollama",
            },
        }
    ]
}

```

Như vậy LiteLLM chỉ expose **một model**.

---

# 9. Cloudflare

Cell cuối:

```
cloudflared tunnel --url http://127.0.0.1:4000 \
  > /tmp/cloudflared.log 2>&1 &

```

Sau đó parse:

```
import re
import time

pattern = r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com"

for _ in range(60):
    with open("/tmp/cloudflared.log") as f:
        log = f.read()

    match = re.search(pattern, log)

    if match:
        public_url = match.group(0)
        break

    time.sleep(1)

print(public_url)

```

---

# 10. Output của notebook

Cuối notebook:

```
╔═══════════════════════════════════════╗
║             MODEL READY               ║
╠═══════════════════════════════════════╣
║ Host       : colab-t4-01              ║
║ GPU        : Tesla T4                 ║
║ VRAM       : 15 GB                    ║
║ Model      : qwen3-8b                 ║
║ Context    : 32768                    ║
║ Runtime    : Ollama                   ║
║ Gateway    : LiteLLM                  ║
║                                       ║
║ Endpoint:                             ║
║ https://xxxxx.trycloudflare.com       ║
╚═══════════════════════════════════════╝

```

---

# 11. `modelctl` trên máy bạn

Đây là phần Cursor sẽ giúp rất nhiều.

CLI:

```
modelctl hosts
modelctl models
modelctl use colab-t4-01 qwen3-8b
modelctl status
modelctl endpoint
modelctl stop

```

Nhưng ở MVP:

```
modelctl use colab-t4-01 qwen3-8b

```

chưa cần tự động start Colab.

Nó chỉ quản lý **local state**:

```
{
  "host": "colab-t4-01",
  "model": "qwen3-8b",
  "endpoint": "https://xxxxx.trycloudflare.com"
}

```

---

# 12. Auto-update Claude Code

Sau khi Colab đưa URL:

```
modelctl endpoint set https://xxxxx.trycloudflare.com

```

CLI update environment/config.

Ví dụ:

```
export ANTHROPIC_BASE_URL="https://xxxxx.trycloudflare.com"
export ANTHROPIC_API_KEY="..."

```

Mình sẽ **không hard-code URL trong repo**.

Local state:

```
~/.modelctl/
├── config.json
├── credentials
└── state.json

```

---

# 13. Cursor integration

Bạn làm việc bằng Cursor thì tạo:

```
AGENTS.md

```

ở root:

```
# Free Model Gateway

## Architecture

This project provides a zero-cost model gateway
for Claude Code and coding clients.

Architecture:

Client
-> Cloudflare Tunnel
-> LiteLLM
-> Ollama
-> exactly one selected model

## Rules

- Never run multiple models simultaneously.
- Never hard-code a Cloudflare URL.
- Model definitions belong in config/models.yaml.
- Host definitions belong in config/hosts.yaml.
- Never put API keys into git.
- Validate GPU VRAM before downloading a model.
- Validate model health before exposing the endpoint.
- Keep Colab bootstrap self-contained.
- Do not introduce a central always-on server for MVP.

## Model lifecycle

One Colab runtime selects exactly one model.

The model is selected before startup.

The notebook must not download or load
unselected models.

## Testing

Run:

pytest

before committing changes.

```

Cái này rất hữu ích vì Cursor sẽ có context liên tục.

---

# 14. Cursor Rules

Nếu Cursor version của bạn hỗ trợ project rules, tạo:

```
.cursor/
└── rules/
    ├── architecture.mdc
    ├── python.mdc
    └── colab.mdc

```

Ví dụ `architecture.mdc`:

```
---
description: Architecture rules for model gateway
alwaysApply: true
---

The system consists of:

1. Client
2. Cloudflare Tunnel
3. LiteLLM
4. Ollama
5. Exactly one model

Never introduce a central gateway server
unless explicitly requested.

Never make model selection and host selection
the same abstraction.

Models belong to models.yaml.

Hosts belong to hosts.yaml.

```

---

# 15. API contract

Mình sẽ chuẩn hóa internal contract ngay từ đầu.

### `/health`

```
GET /health

```

Response:

```
{
  "status": "ok"
}

```

### `/v1/models`

```
GET /v1/models

```

Response:

```
{
  "data": [
    {
      "id": "qwen3-8b",
      "object": "model"
    }
  ]
}

```

### `/v1/chat/completions`

Gateway forward tới Ollama.

Claude Code sẽ giao tiếp qua adapter tương thích Anthropic.

---

# 16. State machine

Mình sẽ định nghĩa host state:

```
OFFLINE
   │
   ▼
STARTING
   │
   ▼
MODEL_LOADING
   │
   ▼
GATEWAY_STARTING
   │
   ▼
TUNNEL_STARTING
   │
   ▼
READY
   │
   ├──────────────┐
   ▼              ▼
ERROR           STOPPING
                  │
                  ▼
                OFFLINE

```

Không dùng kiểu:

```
if running:
    ...

```

lung tung trong code.

Có state machine rõ ràng thì Cursor ít phá architecture hơn.

---

# 17. Health checks

`health.py`:

```
async def wait_for_ollama():
    ...

async def wait_for_model(model):
    ...

async def wait_for_gateway():
    ...

async def wait_for_tunnel():
    ...

```

Pipeline:

```
Ollama healthy
      ↓
Model available
      ↓
Gateway healthy
      ↓
Tunnel available
      ↓
End-to-end request
      ↓
READY

```

**Chỉ print "READY" sau khi test end-to-end thành công.**

---

# 18. End-to-end test

Notebook cuối cùng tự chạy:

```
response = requests.post(
    f"{public_url}/v1/models",
    headers={
        "Authorization": f"Bearer {API_KEY}"
    }
)

assert response.status_code == 200

```

Sau đó:

```
✅ Ollama
✅ Model
✅ LiteLLM
✅ Cloudflare
✅ Public API

```

---

# 19. Resource policy

T4:

```
gpu_profiles:

  t4-16gb:
    vram_gb: 15
    reserved_vram_gb: 2
    usable_vram_gb: 13

```

Mình **không coi toàn bộ 15 GB là model budget**.

Ví dụ:

```
T4
15 GB total
│
├── ~2 GB runtime/system/KV overhead
│
└── ~13 GB model budget

```

Vì thế:

```
qwen3-4b       ✅
qwen3-8b       ✅
qwen3-14b      ⚠️

```

và context sẽ được giới hạn tương ứng.

---

# 20. Context policy

Ví dụ:

```
qwen3-14b:
  default_context: 8192
  max_context: 16384

```

Tức là mặc định:

```
Qwen3 14B
8K context

```

chứ không cố nhồi 32K/64K vào T4.

Đây là điểm rất quan trọng cho coding agent vì **context càng lớn thì KV cache càng ăn VRAM**.

---

# 21. Hugging Face

Sau khi Colab version chạy ổn, HF adapter sẽ implement cùng interface:

```
class HostAdapter(Protocol):

    def start(self, host, model):
        ...

    def stop(self, host):
        ...

    def status(self, host):
        ...

    def endpoint(self, host):
        ...

```

Colab:

```
class ColabAdapter(HostAdapter):
    ...

```

HF:

```
class HuggingFaceAdapter(HostAdapter):
    ...

```

Model layer không thay đổi.

---

# 22. Cái gì KHÔNG nên làm

Mình sẽ tránh 5 thứ ở version 1:

### Không dùng Kubernetes

Overkill.

### Không dùng Redis

Không cần.

### Không dùng database

`state.json` đủ.

### Không chạy nhiều model

Đi ngược mục tiêu VRAM.

### Không làm auto-start Colab ngay

Đây là phần dễ biến project thành nightmare.

---

# 23. Development roadmap cho Cursor

Mình sẽ đưa Cursor từng task nhỏ.

### Sprint 1

```
Task 1
Create project skeleton.

Task 2
Implement models.yaml parser.

Task 3
Implement hosts.yaml parser.

Task 4
Implement model/host compatibility validation.

Task 5
Implement GPU VRAM detection.

```

### Sprint 2

```
Task 6
Create Colab notebook.

Task 7
Install Ollama.

Task 8
Implement selected-model-only startup.

Task 9
Implement model health check.

Task 10
Implement LiteLLM generation.

```

### Sprint 3

```
Task 11
Implement cloudflared startup.

Task 12
Parse trycloudflare URL.

Task 13
End-to-end health check.

Task 14
Print connection information.

```

### Sprint 4

```
Task 15
Implement modelctl.

Task 16
Implement local state.

Task 17
Implement endpoint management.

Task 18
Implement status/list commands.

```

### Sprint 5

```
Task 19
HF adapter.

Task 20
Better error handling.

Task 21
Logs.

Task 22
Tests.

Task 23
Documentation.

```

---

# 24. UX cuối cùng

Sau khi hoàn thành, workflow của bạn sẽ rất đơn giản.

Bạn mở Colab.

Chọn:

```
Host:
Colab T4 #1

Model:
Qwen3 14B

Context:
8K

```

**Run All.**

Đợi:

```
🟢 READY

Model: qwen3-14b
GPU: T4
Endpoint:
https://abc123.trycloudflare.com

```

Sau đó trên PC:

```
modelctl connect https://abc123.trycloudflare.com

```

Rồi Cursor/Claude Code sử dụng endpoint đó.

Muốn đổi model:

```
Runtime → Restart
Model → Qwen3 8B
Run All

```

Muốn đổi host:

```
mở Colab #2
Model → DeepSeek R1 8B
Run All

```

**Không cần domain. Không cần VPS. Không cần chạy nhiều GPU. Không cần một gateway server 24/7.**

---

## Một lưu ý cuối về Cursor

Nếu mục tiêu của bạn là **dùng model local/free trực tiếp trong Cursor**, thì có một quyết định cần chốt trước khi code: **Cursor và Claude Code không nhất thiết có cùng cơ chế custom model endpoint**. Vì vậy mình sẽ coi **Anthropic-compatible gateway là interface chuẩn của hệ thống**, sau đó kiểm tra riêng Cursor hỗ trợ endpoint/model nào trong phiên bản bạn đang dùng, thay vì thiết kế architecture phụ thuộc trực tiếp vào Cursor.

Nếu bạn muốn triển khai ngay bằng Cursor, **Phase 1 nên chỉ làm đúng một vertical slice**:

```
Colab T4
 → Ollama
 → Qwen3 8B
 → LiteLLM
 → Cloudflare Quick Tunnel
 → curl end-to-end

```

Chạy được đường này rồi mới thêm 8 model còn lại và `modelctl`. Đây là cách ít rủi ro nhất để Cursor không xây quá nhiều abstraction trước khi biết backend thực sự hoạt động.