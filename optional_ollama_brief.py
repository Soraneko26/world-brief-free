#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD_JSON = ROOT / "data" / "world.json"
OUT_TXT = ROOT / "data" / "ai_brief.txt"


def main() -> None:
    model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    endpoint = os.getenv("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/generate")
    if not WORLD_JSON.exists():
        raise SystemExit("world.json is missing. run fetch_world_data.py first.")

    payload = json.loads(WORLD_JSON.read_text(encoding="utf-8"))
    sample = payload.get("events", [])[:120]

    prompt = (
        "You are a concise analyst. Summarize the global situation in Japanese in 8 bullets.\n"
        "Use only this JSON subset.\n"
        "Include: trend, risks, and watchpoints.\n\n"
        + json.dumps(sample, ensure_ascii=False)
    )
    req_body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        response = json.loads(resp.read().decode("utf-8"))
    text = response.get("response", "").strip()
    OUT_TXT.write_text(text + "\n", encoding="utf-8")
    print(f"wrote {OUT_TXT}")


if __name__ == "__main__":
    main()
