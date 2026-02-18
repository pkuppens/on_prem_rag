#!/usr/bin/env python3
"""Manual script to test chat streaming with local Ollama.

Chat streaming = LLM provider sends partial results as they are generated,
reducing perceived wait. Uses direct=true to skip RAG and exercise pure
LLM streaming (no document retrieval). Run with backend and Ollama:
  uv run start-backend   # in one terminal
  ollama serve           # (ollama pull mistral if needed)
  uv run python scripts/test_chat_stream_local.py

The script detects whether the provider supports streaming by observing
the response: token events mean streaming; a single answer event means the
backend fell back to non-streaming (provider does not stream).
"""

import json
import os
import sys


def main() -> int:
    """Call /api/chat/stream with direct=true, print output, and report streaming support."""
    try:
        import httpx
    except ImportError:
        print("pip install httpx or uv add httpx", file=sys.stderr)
        return 1

    base = os.getenv("RAG_API_BASE", "http://localhost:9180")
    url = f"{base}/api/chat/stream"

    # direct=true: skip RAG, stream LLM response directly (validates token-by-token streaming)
    payload = {
        "messages": [{"role": "user", "content": "Count from 1 to 10, one number per line. Start now."}],
        "direct": True,
    }

    token_count = 0
    got_answer_event = False

    print(f"POST {url} (direct=true, no RAG)", flush=True)
    with httpx.Client(timeout=60.0) as http:
        with http.stream("POST", url, json=payload) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        t = data.get("type", "")
                        if t == "token":
                            token_count += 1
                            print(data.get("content", ""), end="", flush=True)
                        elif t == "sources":
                            n = data.get("chunks_retrieved", 0)
                            direct = data.get("direct", False)
                            lbl = "Direct (no RAG)" if direct else f"Retrieved {n} chunks"
                            print(f"[{lbl}] ", end="", flush=True)
                        elif t == "answer":
                            got_answer_event = True
                            print(data.get("content", ""), end="", flush=True)
                        elif t == "done":
                            break
                    except json.JSONDecodeError:
                        pass

    print(flush=True)
    if token_count > 0:
        print(f"[Streaming: yes — {token_count} token events received]", flush=True)
    elif got_answer_event:
        print("[Streaming: no — provider delivered full response at once (backend fallback)]", flush=True)
    else:
        print("[Streaming: undetermined — no token or answer events]", flush=True)
    print("[Done]", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
