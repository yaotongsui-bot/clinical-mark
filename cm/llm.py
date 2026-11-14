"""Ollama JSON calls with a cache keyed by the exact request.

The cache is one JSON line per request (the request itself, the answer and the judge's reasoning),
so it also serves as the call log.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = os.environ.get("CLINICAL_MARK_OLLAMA_ENDPOINT", "http://127.0.0.1:11434")
# Models named "<name>:cloud" are called on Ollama's hosted API with OLLAMA_API_KEY. That API ignores
# the "format" schema, so the schema goes into the prompt and the answer is checked against it here.
CLOUD_ENDPOINT = "https://ollama.com"
SEED = 20261011
MAX_CLOUD_PREDICT = 32768


def _is_cloud(model: str) -> bool:
    return model.endswith(":cloud")


def _first_json_object(text: str) -> Any:
    """The first JSON object in a reply that may wrap it in prose or a code fence."""
    decoder = json.JSONDecoder()
    for start, char in enumerate(text):
        if char == "{":
            try:
                return decoder.raw_decode(text[start:])[0]
            except ValueError:
                continue
    raise ValueError("no JSON object in the reply")


def _check(value: Any, schema: dict, path: str = "$") -> None:
    """Required keys, types and enums of the schema subset the prompts use."""
    kind = schema.get("type")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} = {value!r} is not one of {schema['enum']}")
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{path} is not an object")
        for name in schema.get("required", []):
            if name not in value:
                raise ValueError(f"{path} lacks {name!r}")
        for name, sub in schema.get("properties", {}).items():
            if name in value:
                _check(value[name], sub, f"{path}.{name}")
    elif kind == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path} is not an array")
        for i, item in enumerate(value):
            _check(item, schema.get("items", {}), f"{path}[{i}]")
    elif kind == "string" and not isinstance(value, str):
        raise ValueError(f"{path} is not a string")
    elif kind == "boolean" and not isinstance(value, bool):
        raise ValueError(f"{path} is not true/false")


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
        self._lock = threading.Lock()  # the judge panel calls cloud models from several threads

    def _remember(self, key: str, record: dict) -> None:
        with self._lock:
            self.cache[key] = record
            with self.cache_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _post(self, path: str, payload: dict, timeout: int = 900, cloud: bool = False) -> dict:
        headers = {"Content-Type": "application/json"}
        if cloud:
            key = os.environ.get("OLLAMA_API_KEY", "").strip()
            if not key:
                raise RuntimeError("OLLAMA_API_KEY is not set (needed for :cloud models)")
            headers["Authorization"] = f"Bearer {key}"
        request = urllib.request.Request(
            (CLOUD_ENDPOINT if cloud else ENDPOINT).rstrip("/") + path,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")
        # Busy (429) or a server error: back off and retry longer, since several runs may share the
        # plan's concurrent-request limit. Other failures get three tries.
        attempt = 0
        while True:
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as exc:
                busy = isinstance(exc, urllib.error.HTTPError) and (exc.code == 429 or exc.code >= 500)
                attempt += 1
                if attempt >= (8 if busy else 3):
                    raise RuntimeError(f"Ollama request failed: {exc}") from exc
                time.sleep(min(60, 5 * 2 ** (attempt - 1)) if busy else 3 * attempt)

    def json(self, model: str, system: str, user: str, schema: dict, *, num_predict: int = 1200,
             stage: str = "", case_id: str = "", think: bool = False,
             sampling: dict | None = None) -> dict[str, Any]:
        """think=True asks a reasoning-capable model to reason before answering (VeriFact found
        reasoning judges agree better with clinicians). The reasoning text is logged, not returned.
        sampling overrides temperature / top_p / seed (VeriFact's judge uses temperature 0.1 and
        retries with new samples); when given it is part of the cache key."""
        parts = [model, system, user, schema] + (["think"] if think else []) + ([sampling] if sampling else [])
        key = json.dumps(parts, ensure_ascii=False)
        if key in self.cache:
            with self._lock:
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
        if sampling:
            options.update(sampling)
        cloud = _is_cloud(model)
        if cloud:
            system += ("\n\nReply with ONE JSON object and nothing else (no prose, no code fence). It must "
                       "match this JSON schema:\n" + json.dumps(schema, ensure_ascii=False))
        payload = {
            "model": model.removesuffix(":cloud"), "stream": False, "format": schema, "think": think,
            "keep_alive": "10m", "options": options,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        # Without schema-constrained decoding a cloud answer can miss a field; it gets two corrections.
        for attempt in range(3 if cloud else 1):
            started = time.time()
            body = self._post("/api/chat", payload, cloud=cloud)
            raw = str(body.get("message", {}).get("content", "")).strip()
            with self._lock:
                self.calls += 1
            record = {"stage": stage, "case_id": case_id, "elapsed_seconds": round(time.time() - started, 2),
                      "request": parts, "reasoning": body.get("message", {}).get("thinking"),
                      "done_reason": body.get("done_reason"), "raw_response": raw}
            try:
                response = _first_json_object(raw) if cloud else json.loads(raw)
                if not isinstance(response, dict):
                    raise ValueError("not a JSON object")
                if cloud:
                    _check(response, schema)
            except ValueError as exc:  # json.JSONDecodeError is a ValueError
                if attempt + 1 < (3 if cloud else 1):
                    # Some models reason even with think off and use up the output budget: same request, more room.
                    if body.get("done_reason") == "length" and options["num_predict"] < MAX_CLOUD_PREDICT:
                        options["num_predict"] = min(MAX_CLOUD_PREDICT, options["num_predict"] * 4)
                        continue
                    if raw:  # the hosted API rejects an empty assistant message with HTTP 400
                        payload["messages"].append({"role": "assistant", "content": raw})
                    payload["messages"].append({"role": "user", "content": f"That reply is invalid: {exc}. "
                                                "Return the corrected JSON object only, with every required field."})
                    continue
                if think:  # seeded sampling: remember the failure instead of paying for it on every rerun
                    self._remember(key, {**record, "failed": True, "response": None})
                raise ValueError(f"{model} returned invalid JSON ({exc}): {raw[:200]!r}") from exc
            self._remember(key, {**record, "attempts": attempt + 1, "response": response} if cloud
                           else {**record, "response": response})
            return response
        raise AssertionError("unreachable")

    def unload(self, model: str) -> None:
        """Free GPU memory before another model is loaded."""
        if _is_cloud(model):
            return
        try:
            self._post("/api/generate", {"model": model, "keep_alive": 0}, timeout=60)
        except RuntimeError:
            pass
