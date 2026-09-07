#!/usr/bin/env python3
"""Extract privacy-reduced workflow seeds from a ChatGPT-style JSON export."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), "<email>"),
    (re.compile(r"https?://\S+"), "<url>"),
    (re.compile(r"/(?:Users|home)/[^\s\"']+"), "<local-path>"),
    (re.compile(r"\b(?:sk|api|token|secret|key)[-_][A-Za-z0-9_-]{12,}\b", re.I), "<secret>"),
]
TOOL_WORDS = ("search", "read", "write", "edit", "delete", "commit", "push", "deploy", "render", "download", "email", "calendar", "browser")


def redact(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text[:600]


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key.lower() not in {"id", "uuid", "account_id"}:
                yield from strings(item)


def seeds(payload: Any) -> list[dict[str, Any]]:
    conversations = payload if isinstance(payload, list) else payload.get("conversations", [payload])
    output = []
    for item in conversations:
        text = "\n".join(strings(item))
        if not text.strip():
            continue
        safe = redact(text)
        tools = sorted({word for word in TOOL_WORDS if re.search(rf"\b{word}\w*\b", text, re.I)})
        output.append({
            "seed_id": hashlib.sha256(safe.encode()).hexdigest()[:12],
            "intent_excerpt": safe,
            "tool_classes": tools,
            "requires_review": True,
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = seeds(json.loads(args.input.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {len(result)} privacy-reduced seeds; manual review is required")


if __name__ == "__main__":
    main()
