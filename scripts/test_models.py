#!/usr/bin/env python3
"""Test which models are accessible on the Element LLM Gateway.

Run this whenever you need to verify model access or debug
connection issues. Uses the native endpoint per provider.

Usage:
    python scripts/test_models.py
    python scripts/test_models.py --model claude-opus-4-6
"""

import os
import sys
import time
import urllib3

import httpx
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings()


ALL_MODELS = [
    # Anthropic (latest first)
    "claude-opus-4-6",
    "claude-opus-4-5",
    "claude-sonnet-4-6",
    "claude-sonnet-4-5",
    "claude-opus-4",
    "claude-sonnet-4",
    # OpenAI (latest first)
    "gpt-5.2",
    "gpt-4.1",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-4o-mini",
    "gpt-4.1-nano",
    "o3",
    # Google (latest first)
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]


def _detect_provider(model: str) -> str:
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gemini"):
        return "google"
    return "openai"


def _test_model(
    client: httpx.Client, base_url: str, model: str,
) -> tuple[bool, str]:
    """Test a single model. Returns (success, message)."""
    provider = _detect_provider(model)
    prompt = "Say hi in exactly 3 words"

    if provider == "anthropic":
        url = f"{base_url}/v1/messages"
        body = {
            "model": model,
            "max_tokens": 20,
            "messages": [{"role": "user", "content": prompt}],
        }
    elif provider == "google":
        url = f"{base_url}/v1/models/{model}:generateContent"
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "maxOutputTokens": 20,
                "temperature": 0.1,
            },
        }
    else:  # openai
        url = f"{base_url}/v1/chat/completions"
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 20,
        }

    try:
        r = client.post(url, json=body)
        if r.status_code == 200:
            data = r.json()
            if provider == "anthropic":
                text = data["content"][0]["text"]
            elif provider == "google":
                text = (
                    data["candidates"][0]["content"]["parts"][0]["text"]
                )
            else:
                text = data["choices"][0]["message"]["content"]
            return True, text.strip()[:40]
        elif r.status_code == 429:
            return True, "RATE LIMITED (model exists)"
        else:
            return False, f"{r.status_code}: {r.text[:80]}"
    except Exception as e:
        return False, str(e)[:80]


def main() -> None:
    key = os.getenv("ELEMENT_API_KEY")
    url = os.getenv("ELEMENT_GATEWAY_URL")
    if not key or not url:
        print("❌ ELEMENT_API_KEY and ELEMENT_GATEWAY_URL must be set")
        sys.exit(1)

    client = httpx.Client(
        verify=False,
        headers={
            "Authorization": f"Bearer {key}",
            "WM_CONSUMER.ID": "promotionbench",
            "WM_SVC.NAME": "promotionbench",
            "WM_SVC.ENV": "stg",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(30.0, connect=10.0),
    )

    # Single model test or full scan
    models = ALL_MODELS
    if len(sys.argv) > 2 and sys.argv[1] == "--model":
        models = [sys.argv[2]]

    print(f"Gateway: {url}")
    print(f"Testing {len(models)} models...\n")

    working = []
    for model in models:
        provider = _detect_provider(model)
        ok, msg = _test_model(client, url, model)
        icon = "✅" if ok else "❌"
        print(f"  {icon} {model:<25s} ({provider:<10s}) → {msg}")
        if ok:
            working.append(model)
        time.sleep(0.5)  # Be gentle with rate limits

    print(f"\n{len(working)}/{len(models)} models accessible")


if __name__ == "__main__":
    main()
