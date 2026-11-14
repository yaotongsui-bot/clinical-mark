"""A panel of judge models from different families; the majority label wins.

Follows "Replacing Judges with Juries" (Verga et al., 2024): several smaller models from disjoint
families disagree less systematically than one judge. Models listed in `think` answer in reasoning
mode, which VeriFact (Chung et al., NEJM AI 2026) found to improve agreement with clinicians.
Each model answers every pending request before the next model is loaded, so the GPU swaps models
once per stage, not once per request. A cloud model ("<name>:cloud") gets several requests at once
(Ollama's plans allow 3 concurrent requests); each answer depends only on its own request, so the
verdicts are the same as sending them one by one.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .llm import SEED

_ID = re.compile(r"\bR\d+\b")
FALLBACK_WORKERS = 3  # concurrent requests every Ollama plan allows


@dataclass
class Request:
    key: str
    stage: str
    case_id: str
    system: str
    user: str
    schema: dict
    cite_key: str              # "evidence" (list of ids) or "match" (one id or null)
    needs_cite: set[str]       # labels that must cite at least one supplied id
    allowed: set[str]          # supplied ids
    fallback: str              # label used when the panel splits
    votes: dict = field(default_factory=dict)
    # VeriFact-style judging: parse(answer) -> {"label", "reason"} or ValueError; a rejected answer is
    # sampled again (up to `attempts`) with `sampling` and a new seed each time.
    parse: Callable[[dict], dict] | None = None
    attempts: int = 2
    sampling: dict | None = None


def _cited_ids(raw, allowed: set[str]) -> list[str]:
    """Supplied ids from a citation field; models sometimes write 'R2: Given heparin' instead of 'R2'."""
    items = raw if isinstance(raw, list) else [raw]
    found = [m for item in items if item for m in _ID.findall(str(item))]
    return [c for c in dict.fromkeys(found) if c in allowed]


class Panel:
    def __init__(self, llm, models: list[str], think: set[str] | None = None, cloud_workers: int = 1):
        self.llm = llm
        self.models = models
        self.think = think or set()
        self.cloud_workers = max(1, cloud_workers)
        self.requests: dict[str, Request] = {}

    def submit(self, request: Request) -> None:
        self.requests[request.key] = request

    def _ask(self, model: str, req: Request) -> dict | None:
        user = req.user
        think = model in self.think
        if req.parse:
            for attempt in range(req.attempts):
                sampling = {**(req.sampling or {}), "seed": SEED + attempt} if req.sampling else None
                try:
                    out = self.llm.json(model, req.system, user, req.schema, num_predict=500,
                                        stage=f"{req.stage}:{model}", case_id=req.case_id, think=think,
                                        sampling=sampling)
                    parsed = req.parse(out)
                except ValueError:
                    continue
                return {"label": parsed["label"], "cites": [], "reason": parsed.get("reason", "")}
            return None
        for _ in range(2):
            try:
                out = self.llm.json(model, req.system, user, req.schema, num_predict=500,
                                    stage=f"{req.stage}:{model}", case_id=req.case_id, think=think)
            except ValueError:  # empty or unparsable answer: this judge abstains
                return None
            cites = _cited_ids(out.get(req.cite_key), req.allowed)
            if out.get("label") not in req.needs_cite or cites:
                return {"label": out.get("label"), "cites": cites, "reason": out.get("reason", "")}
            user += (f"\nThe label {out.get('label')} must cite a supplied id in '{req.cite_key}'. "
                     "Re-evaluate and return corrected JSON.")
        return None

    def run(self) -> None:
        for model in self.models:
            reqs = list(self.requests.values())
            workers = self.cloud_workers if model.endswith(":cloud") else 1
            if workers == 1:
                for req in reqs:
                    req.votes[model] = self._ask(model, req)
            else:
                try:
                    self._ask_parallel(model, reqs, workers)
                except RuntimeError as exc:  # e.g. HTTP 429: the plan allows fewer requests at once
                    if workers <= FALLBACK_WORKERS:
                        raise
                    print(f"{model}: {exc}; retrying with {FALLBACK_WORKERS} requests at once", flush=True)
                    self.cloud_workers = FALLBACK_WORKERS
                    self._ask_parallel(model, reqs, FALLBACK_WORKERS)  # answers already in the cache are reused
            self.llm.unload(model)

    def _ask_parallel(self, model: str, reqs: list[Request], workers: int) -> None:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for req, vote in zip(reqs, pool.map(lambda r: self._ask(model, r), reqs)):
                req.votes[model] = vote

    def verdict(self, key: str) -> dict:
        req = self.requests[key]
        own = {m: v for m, v in req.votes.items() if m in self.models}
        valid = {m: v for m, v in own.items() if v}
        counts = Counter(v["label"] for v in valid.values())
        votes = {m: (v["label"] if v else None) for m, v in own.items()}
        if counts:
            label, n = counts.most_common(1)[0]
            if n * 2 > len(self.models):
                majority = [v for v in valid.values() if v["label"] == label]
                cites = list(dict.fromkeys(c for v in majority for c in v["cites"]))
                return {"label": label, "agreement": f"{n}/{len(self.models)}", "votes": votes,
                        "reason": majority[0]["reason"], "cites": cites}
        return {"label": req.fallback, "agreement": "split", "votes": votes, "cites": [],
                "reason": "The judges disagreed; the conservative label was used and the item needs human review."}
