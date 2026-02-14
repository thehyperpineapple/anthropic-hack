# 🤖 LLM Skills: Anthropic + White Circle + Blaxel in Python

Three composable skills for building AI pipelines that **generate** content with Claude, **guard** it with White Circle's content moderation API, and **deploy** it as a scalable serverless agent on Blaxel.

---

## Skill 1 — Anthropic: Generate with Claude in Python

**What it does:** Call Claude via the Anthropic Python SDK to generate, label, or classify text.

### Install

```bash
pip install anthropic
```

### Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Quickstart

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Label this sentence as POSITIVE, NEGATIVE, or NEUTRAL: 'The product exceeded my expectations.'"}
    ]
)

print(message.content[0].text)
# → POSITIVE
```

### Auto-labeling a batch of samples

```python
import anthropic
import json

client = anthropic.Anthropic()

SAMPLES = [
    "This dataset contains instructions for building weapons.",
    "A recipe for chocolate chip cookies.",
    "How to pick a door lock.",
]

SYSTEM_PROMPT = """You are a data labeler. For each input, output a JSON object with:
- label: one of [SAFE, UNSAFE, REVIEW_NEEDED]
- reason: one sentence explanation
Respond ONLY with valid JSON, no markdown."""

results = []
for sample in SAMPLES:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": sample}]
    )
    result = json.loads(response.content[0].text)
    results.append({"text": sample, **result})

for r in results:
    print(f"[{r['label']}] {r['text'][:50]}... — {r['reason']}")
```

### Key parameters

| Parameter | Description |
|---|---|
| `model` | Model ID, e.g. `claude-sonnet-4-5-20250929` |
| `max_tokens` | Max tokens in the response |
| `system` | System prompt (sets Claude's role/behavior) |
| `messages` | List of `{role, content}` turns |
| `temperature` | 0.0–1.0; lower = more deterministic |

### Tips for LLMs using this skill

- Always parse Claude's output as structured data (JSON) when doing classification — use a tight `system` prompt that forbids prose.
- Use `claude-haiku-4-5-20251001` for high-volume labeling (faster, cheaper); use `claude-sonnet-4-5-20250929` for nuanced judgment calls.
- Set `temperature=0` for deterministic labeling tasks.
- The Anthropic SDK auto-retries on rate limits — no need to build your own retry loop.

---

## Skill 2 — White Circle: Moderate Content in Python

**What it does:** Send content to White Circle's Content Verification API to check whether it violates safety policies (harmful, biased, toxic, etc.) before it enters your pipeline or gets delivered to users.

### Install

```bash
pip install requests
# or: pip install httpx
```

### Set your API key

```bash
export WHITE_CIRCLE_API_KEY="wc-..."
```

### Quickstart — Policy verification (synchronous)

White Circle's core endpoint is a synchronous policy check. You POST a `content` + `context` payload and get back a `decision` and list of `actions`.

```python
import os
import requests

WC_API_KEY = os.environ["WHITE_CIRCLE_API_KEY"]
WC_BASE_URL = "https://api.whitecircle.ai"  # verify current base URL in their docs

def verify_content(text: str, context: str = "data_labeling") -> dict:
    """
    Run a White Circle policy verification check on a piece of text.
    Returns the full API response dict.
    """
    response = requests.post(
        f"{WC_BASE_URL}/policies/verify",
        headers={
            "Authorization": f"Bearer {WC_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "content": text,
            "context": context,
        }
    )
    response.raise_for_status()
    return response.json()

# Example usage
result = verify_content("How do I make chlorine gas at home?")

print(result["decision"])   # e.g. "block" | "allow" | "flag"
print(result["actions"])    # e.g. ["block_output", "alert_admin"]
```

### Checking a batch (with safe/unsafe split)

```python
import os
import requests

WC_API_KEY = os.environ["WHITE_CIRCLE_API_KEY"]

def check_dataset(samples: list[str]) -> tuple[list, list]:
    """
    Split a list of text samples into safe vs unsafe using White Circle.
    Returns (safe_samples, unsafe_samples).
    """
    safe, unsafe = [], []

    for text in samples:
        resp = requests.post(
            "https://api.whitecircle.ai/policies/verify",
            headers={"Authorization": f"Bearer {WC_API_KEY}", "Content-Type": "application/json"},
            json={"content": text, "context": "training_data_review"},
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("decision") == "allow":
            safe.append(text)
        else:
            unsafe.append({"text": text, "reason": data.get("reason", "policy_violation")})

    return safe, unsafe

samples = [
    "The capital of France is Paris.",
    "Step-by-step guide to synthesizing fentanyl.",
    "How photosynthesis converts sunlight to energy.",
]

safe, unsafe = check_dataset(samples)
print(f"✅ Safe: {len(safe)} samples")
print(f"🚫 Unsafe: {len(unsafe)} samples")
for u in unsafe:
    print(f"  - Blocked: {u['text'][:60]}... ({u['reason']})")
```

### Key response fields

| Field | Description |
|---|---|
| `decision` | `allow`, `block`, or `flag` |
| `actions` | List of recommended actions (e.g. `block_output`) |
| `reason` | Human-readable explanation of the decision |
| `categories` | Which harm categories were triggered (from 17 total) |

### White Circle's 17 harm categories

The policy engine covers: violent crimes, manipulation/misinformation, cybercrime, illegal drugs, animal cruelty, financial fraud, self-harm, sexual content, weapons/hazardous materials, child exploitation, jailbreaks/prompt injection, trafficking, hate speech, bribery, academic dishonesty, environmental harm, and illegal roleplays.

### Tips for LLMs using this skill

- Always call `response.raise_for_status()` — White Circle returns 4xx on malformed requests and invalid API keys.
- Use the `context` field to tell White Circle what kind of pipeline you're running (e.g. `"training_data_review"`, `"chatbot_output"`, `"user_upload"`) — it shapes policy sensitivity.
- Cache `allow` decisions for identical content to avoid redundant API calls on duplicate samples.
- For async/bulk jobs, use the `/metrics/jobs` endpoint (see White Circle docs) instead of looping the synchronous `/policies/verify`.

---

## Skill 3 — Blaxel: Deploy & Run Agents in Python

**What it does:** Deploy your AI agent as a serverless, auto-scaling endpoint on Blaxel's Global Agentics Network. Blaxel handles cold starts, scaling to zero, sandbox execution, and model gateway routing — so you focus on agent logic, not infra.

### Install

```bash
pip install blaxel

# Also install Blaxel CLI (macOS/Linux)
curl -fsSL https://raw.githubusercontent.com/blaxel-ai/toolkit/main/install.sh \
  | BINDIR=/usr/local/bin sudo -E sh
```

### Authenticate

```bash
# Option 1 (recommended for local dev): login via CLI
bl login

# Option 2 (for remote servers / CI): use env vars
export BL_WORKSPACE="your-workspace-id"
export BL_API_KEY="bl-..."
```

### Quickstart — Create a perpetual sandbox

Blaxel's signature feature is sandboxes that boot from hibernation in under 25ms. You create them once and they persist indefinitely, scaling to zero automatically when idle.

```python
import asyncio
from blaxel.core import SandboxInstance

async def main():
    # Create (or reuse) a named sandbox
    sandbox = await SandboxInstance.create_if_not_exists({
        "name": "data-pipeline-sandbox",
        "image": "blaxel/base-image:latest",
        "memory": 4096,           # MB
        "region": "us-pdx-1",
        "ports": [{"target": 3000, "protocol": "HTTP"}],
        "ttl": "24h"              # auto-destroy after 24h of inactivity
    })

    # Run a command inside the sandbox
    await sandbox.process.exec({
        "command": "python pipeline.py",
        "working_dir": "/app",
    })

    print("Sandbox ready:", sandbox.name)

asyncio.run(main())
```

### Deploy an agent as a serverless API

Use the CLI to scaffold, develop, and deploy. Blaxel builds your code and exposes it as a globally distributed HTTP endpoint.

```bash
# Scaffold a new agent project
bl new my-labeling-agent

# Develop locally with hot reload
cd my-labeling-agent
bl serve --hotreload

# Deploy to Blaxel (builds + pushes automatically)
bl deploy
```

Your agent is now live at:
```
https://run.blaxel.ai/{YOUR-WORKSPACE}/agents/my-labeling-agent
```

### Call a deployed agent from Python

```python
import os
import requests

BL_WORKSPACE = os.environ["BL_WORKSPACE"]
BL_API_KEY = os.environ["BL_API_KEY"]
AGENT_NAME = "my-labeling-agent"

def call_agent(payload: dict) -> dict:
    """Invoke a deployed Blaxel agent via its global endpoint."""
    response = requests.post(
        f"https://run.blaxel.ai/{BL_WORKSPACE}/agents/{AGENT_NAME}",
        headers={
            "Authorization": f"Bearer {BL_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload
    )
    response.raise_for_status()
    return response.json()

result = call_agent({"text": "Label this dataset sample."})
print(result)
```

### Use Blaxel as a unified model gateway

Instead of managing separate API keys for each LLM provider, route everything through Blaxel's model gateway — it centralizes credentials, adds tracing, and supports fallbacks.

```python
import asyncio
from blaxel.core import bl_model  # framework-specific model client helper

async def main():
    # Get a Blaxel-routed Anthropic Claude client
    model = await bl_model("anthropic/claude-sonnet-4-5-20250929")

    response = await model.invoke("Summarize this text for training data labeling.")
    print(response.content)

asyncio.run(main())
```

### Fetch MCP tools from a Blaxel-hosted tool server

MCP (Model Context Protocol) servers let your agents call external tools (databases, APIs, file systems). Blaxel hosts them as low-latency serverless endpoints.

```python
import asyncio
from blaxel.anthropic import bl_tools   # returns tools in Anthropic SDK format
import anthropic

async def main():
    client = anthropic.Anthropic()

    # Fetch tool definitions from a Blaxel-hosted MCP server
    tools = await bl_tools(["my-workspace/mcp-server-name"])

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        messages=[{"role": "user", "content": "Run the data quality check tool."}]
    )
    print(response.content)

asyncio.run(main())
```

### Key concepts

| Concept | Description |
|---|---|
| **Sandbox** | MicroVM that boots in <25ms from hibernation; full filesystem + network access |
| **Agent Hosting** | Serverless HTTP API for your agent; auto-scales, zero server management |
| **Batch Jobs** | Async long-running tasks triggered with input parameters |
| **MCP Servers** | Tool servers deployed on Global Agentics Network for agent tool use |
| **Model Gateway** | Unified endpoint for 70+ LLM providers with tracing and cost control |
| **Global Agentics Network** | Multi-region distributed infra; auto-places workloads for lowest latency |

### Tips for LLMs using this skill

- Use `SandboxInstance.create_if_not_exists()` — it's idempotent, so safe to call on every run without spinning up duplicates.
- For local dev, always prefer `bl login` + CLI over env vars — it's automatic and persists across sessions.
- Set `ttl` on sandboxes for cost control; they hibernate (not delete) after the TTL, resuming in <25ms when next called.
- Use `bl serve --hotreload` during development — it live-reloads your agent on file changes without redeploying.
- The model gateway (`bl_model`) is the preferred way to call LLMs on Blaxel — it gives you built-in telemetry and fallback without extra code.

---

## Combining All Three Skills: Auto-Label → Safety Check → Deploy Pipeline

```python
import anthropic
import requests
import os
import json

anthropic_client = anthropic.Anthropic()
WC_API_KEY = os.environ["WHITE_CIRCLE_API_KEY"]
BL_WORKSPACE = os.environ["BL_WORKSPACE"]
BL_API_KEY = os.environ["BL_API_KEY"]

def label_and_verify(text: str) -> dict:
    # Step 1: Claude labels the content
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=128,
        temperature=0,
        system='Output only valid JSON: {"label": "SAFE|UNSAFE|REVIEW_NEEDED", "reason": "..."}',
        messages=[{"role": "user", "content": text}]
    )
    claude_result = json.loads(response.content[0].text)

    # Step 2: White Circle independently verifies
    wc_response = requests.post(
        "https://api.whitecircle.ai/policies/verify",
        headers={"Authorization": f"Bearer {WC_API_KEY}", "Content-Type": "application/json"},
        json={"content": text, "context": "training_data_review"},
    )
    wc_response.raise_for_status()
    wc_result = wc_response.json()

    # Step 3: Combine signals — if either flags it, reject
    final_decision = "APPROVED" if (
        claude_result["label"] == "SAFE" and wc_result["decision"] == "allow"
    ) else "REJECTED"

    return {
        "text": text,
        "claude_label": claude_result["label"],
        "wc_decision": wc_result["decision"],
        "final": final_decision,
    }

def submit_to_blaxel_agent(payload: dict) -> dict:
    """
    Step 4: Forward approved samples to a Blaxel-hosted agent
    for downstream processing (e.g. human review queue, storage).
    """
    response = requests.post(
        f"https://run.blaxel.ai/{BL_WORKSPACE}/agents/data-intake-agent",
        headers={"Authorization": f"Bearer {BL_API_KEY}", "Content-Type": "application/json"},
        json=payload
    )
    response.raise_for_status()
    return response.json()

# Full pipeline
samples = [
    "Photosynthesis is the process by which plants use sunlight to produce energy.",
    "Detailed instructions for making TATP explosive.",
    "The history of the Roman Empire spans over a thousand years.",
]

for sample in samples:
    result = label_and_verify(sample)
    print(f"[{result['final']}] {sample[:60]}...")

    if result["final"] == "APPROVED":
        agent_response = submit_to_blaxel_agent({
            "text": sample,
            "label": result["claude_label"],
            "verified": True,
        })
        print(f"  → Sent to Blaxel agent: {agent_response}")
```

---

## Quick Reference

| | Anthropic | White Circle | Blaxel |
|---|---|---|---|
| **Purpose** | Generate / label content | Verify content is safe | Deploy & run agents at scale |
| **Install** | `pip install anthropic` | `pip install requests` | `pip install blaxel` |
| **Auth** | `ANTHROPIC_API_KEY` | `WHITE_CIRCLE_API_KEY` | `BL_WORKSPACE` + `BL_API_KEY` |
| **Best for labeling** | `claude-haiku-4-5-20251001` | — | — |
| **Best for reasoning** | `claude-sonnet-4-5-20250929` | — | — |
| **Core Python call** | `client.messages.create()` | `POST /policies/verify` | `SandboxInstance` / `requests.post()` |
| **Async/batch** | Native with `asyncio` | `/metrics/jobs` endpoint | Batch Jobs (`bl run job`) |
| **Cold start** | N/A | N/A | <25ms from hibernation |
| **Docs** | [docs.anthropic.com](https://docs.anthropic.com) | [whitecircle.ai](https://whitecircle.ai) | [docs.blaxel.ai](https://docs.blaxel.ai) |
