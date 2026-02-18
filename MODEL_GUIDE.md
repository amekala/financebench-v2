# Model Guide — Element LLM Gateway

> **Last verified: February 2026**
> **Gateway: `wmtllmgateway.stage.walmart.com`**

This document captures the hard-won knowledge of how to correctly call
foundational models through Walmart's Element LLM Gateway. **Do not skip
this file.** Future instances of Code Puppy, agents, or humans touching
this codebase must read this first.

---

## The #1 Mistake (Don't Repeat It)

The Azure OpenAI SDK (`openai.AzureOpenAI` + `api-key` header) **only
works for OpenAI models**. Anthropic and Google models route through
**Vertex AI** and need their own native endpoints. Using the Azure SDK
for Claude/Gemini gives a cryptic `500: Failed to invoke endpoint`.

---

## How to Call Each Provider

### Shared Headers (ALL providers)

```
Authorization: Bearer {ELEMENT_API_KEY}
WM_CONSUMER.ID: promotionbench
WM_SVC.NAME: promotionbench
WM_SVC.ENV: stg
Content-Type: application/json
```

**SSL**: Disabled (`verify=False`) — Walmart internal certs.

### 1. OpenAI Models

**Endpoint**: `POST {GATEWAY_URL}/v1/chat/completions`

```json
{
  "model": "gpt-5.2",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "max_completion_tokens": 1024,
  "temperature": 0.5
}
```

**⚠️ Critical**: Newer models (`gpt-5*`, `o3`, `o4`) require
`max_completion_tokens`. Older models (`gpt-4.1`, `gpt-4o`) accept
`max_tokens`. When in doubt, use `max_completion_tokens`.

### 2. Anthropic Models (Claude)

**Endpoint**: `POST {GATEWAY_URL}/v1/messages`

```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 1024,
  "system": "You are a helpful assistant.",
  "messages": [
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.5
}
```

**Note**: System prompt goes in the top-level `"system"` field, NOT as a
message with `role: system`.

### 3. Google Models (Gemini)

**Endpoint**: `POST {GATEWAY_URL}/v1/models/{MODEL}:generateContent`

```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "..."}]}
  ],
  "system_instruction": {
    "parts": [{"text": "You are a helpful assistant."}]
  },
  "generationConfig": {
    "maxOutputTokens": 1024,
    "temperature": 0.5
  }
}
```

**Note**: Model name goes in the URL path, not the body. System prompt
goes in `system_instruction`.

---

## Verified Working Models (Feb 2026)

### Anthropic (via Vertex AI)

| Deployment Name | Status | Notes |
|---|---|---|
| `claude-opus-4-6` | ✅ Latest | Most capable — protagonist |
| `claude-opus-4-5` | ✅ | Previous flagship |
| `claude-sonnet-4-6` | ✅ | Latest mid-tier |
| `claude-sonnet-4-5` | ✅ | Previous mid-tier |
| `claude-opus-4` | ✅ | Base opus |
| `claude-sonnet-4` | ✅ | Base sonnet |

### OpenAI (via Azure)

| Deployment Name | Status | Notes |
|---|---|---|
| `gpt-5.2` | ✅ Latest | Uses `max_completion_tokens` |
| `gpt-4.1` | ✅ | Uses `max_tokens` or `max_completion_tokens` |
| `gpt-4o` | ✅ | Retiring soon |
| `gpt-4.1-mini` | ✅ | Efficient |
| `gpt-4o-mini` | ✅ | Efficient, retiring |
| `gpt-4.1-nano` | ✅ | Lightest |
| `o3` | ✅ | Reasoning — uses `max_completion_tokens` |

### Google (via Vertex AI)

| Deployment Name | Status | Notes |
|---|---|---|
| `gemini-3-pro-preview` | ⚠️ Latest | **Severe rate limits** — unusable for simulations |
| `gemini-2.5-pro` | ✅ Recommended | Stable flagship, no rate issues |
| `gemini-2.5-flash` | ✅ | Fast |

---

## How We Discovered This

The discovery process (preserved for future debugging):

1. **Azure SDK failed for Claude/Gemini** — `500: Failed to invoke endpoint`
2. **Checked `/Users/a0m14pe/Documents/AI-projects/web-search-agent`** —
   found it uses `Authorization: Bearer` + native endpoints + Walmart
   routing headers (`WM_CONSUMER.ID`, `WM_SVC.NAME`, `WM_SVC.ENV`)
3. **Tested native endpoints** — Claude via `/v1/messages`, Gemini via
   `/v1/models/{m}:generateContent`, OpenAI via `/v1/chat/completions`
4. **All three providers worked** with Bearer auth + routing headers
5. **GPT-5.2 needed `max_completion_tokens`** (not `max_tokens`) — 400 error
6. **Gemini-3-pro-preview** returns 429 under load (rate limited) but exists

### The Test Script

To verify model access, run `scripts/test_models.py` (see below).

---

## Environment Variables

Model assignments are controlled via `.env`. Every character and the
Game Master can be overridden:

```bash
# Gateway connection
ELEMENT_API_KEY=your-jwt-here
ELEMENT_GATEWAY_URL=https://wmtllmgateway.stage.walmart.com/wmtllmgateway

# Character model assignments (override any in .env)
MODEL_RILEY=claude-opus-4-6
MODEL_KAREN=claude-sonnet-4-5
MODEL_DAVID=gemini-3-pro-preview
MODEL_PRIYA=gpt-5.2
MODEL_MARCUS=gpt-5.2
MODEL_GAME_MASTER=claude-opus-4-5

# Simulation variant: "neutral" or "ruthless"
SIMULATION_VARIANT=neutral
```

To swap a model for a run: change ONE line in `.env`, re-run.
No code changes needed.

---

## Quick Reference: Provider Detection

```python
def detect_provider(model_name: str) -> str:
    if model_name.startswith("claude"):  return "anthropic"
    if model_name.startswith("gemini"):  return "google"
    return "openai"
```

The `ElementLanguageModel` class in `financebench/model.py` auto-detects
the provider from the model name and routes to the correct endpoint.
