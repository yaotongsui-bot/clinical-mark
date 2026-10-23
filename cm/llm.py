"""Ollama JSON calls with a cache keyed by the exact request.

The cache is one JSON line per request (the request itself, the answer and the judge's reasoning),
so it also serves as the call log.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = os.environ.get("CLINICAL_MARK_OLLAMA_ENDPOINT", "http://127.0.0.1:11434")
SEED = 20261011


class LLM:
    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache: dict[str, dict] = {}
        if cache_path.exists():
            for line in cache_path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                self.cache[json.dumps(record["request"], ensure_ascii=False)] = record
        self.calls = 0
        self.cache_hits = 0

    def _remember(self, key: str, record: dict) -> None:
        self.cache[key] = record
        with self.cache_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _post(self, path: str, payload: dict, timeout: int = 900) -> dict:
        request = urllib.request.Request(
            ENDPOINT.rstrip("/") + path,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 2:
                    raise RuntimeError(f"Ollama request failed: {exc}") from exc
                time.sleep(3 * (attempt + 1))
        raise AssertionError("unreachable")

    def json(self, model: str, system: str, user: str, schema: dict, *, num_predict: int = 1200,
             stage: str = "", case_id: str = "", think: bool = False) -> dict[str, Any]:
        """think=True asks a reasoning-capable model to reason before answering (VeriFact found
        reasoning judges agree better with clinicians). The reasoning text is logged, not returned."""
        parts = [model, system, user, schema] + (["think"] if think else [])
        key = json.dumps(parts, ensure_ascii=False)
        if key in self.cache:
            self.cache_hits += 1
            record = self.cache[key]
            if record.get("failed"):  # a seeded call that failed before fails the same way again
                raise ValueError(f"{model} failed on this request before: {record['raw_response'][:200]!r}")
            return record["response"]
        options = {"temperature": 0, "seed": SEED, "num_ctx": 16384, "num_predict": num_predict}
        if think:
            # Greedy decoding makes reasoning models loop ("Wait, I should check ..." until the token
            # limit); the usual reasoning-model setting avoids it and the fixed seed keeps it repeatable.
            # The reasoning text counts against the output budget.
            options.update(temperature=0.6, top_p=0.95, num_ctx=32768, num_predict=max(num_predict, 8192))
        payload = {
            "model": model, "stream": False, "format": schema, "think": think, "keep_alive": "10m",
            "options": options,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        started = time.time()
        body = self._post("/api/chat", payload)
        raw = str(body.get("message", {}).get("content", "")).strip()
        self.calls += 1
        record = {"stage": stage, "case_id": case_id, "elapsed_seconds": round(time.time() - started, 2),
                  "request": parts, "reasoning": body.get("message", {}).get("thinking"),
                  "done_reason": body.get("done_reason"), "raw_response": raw}
        try:
            response = json.loads(raw)
            if not isinstance(response, dict):
                raise ValueError("not a JSON object")
        except ValueError as exc:  # json.JSONDecodeError is a ValueError
            if think:  # seeded sampling: remember the failure instead of paying for it on every rerun
                self._remember(key, {**record, "failed": True, "response": None})
            raise ValueError(f"{model} returned invalid JSON ({exc}): {raw[:200]!r}") from exc
        self._remember(key, {**record, "response": response})
        return response

    def unload(self, model: str) -> None:
        """Free GPU memory before another model is loaded."""
        try:
            self._post("/api/generate", {"model": model, "keep_alive": 0}, timeout=60)
        except RuntimeError:
            pass
