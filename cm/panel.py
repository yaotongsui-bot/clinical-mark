"""A panel of judge models from different families; the majority label wins.

Follows "Replacing Judges with Juries" (Verga et al., 2024): several smaller models from disjoint
families disagree less systematically than one judge. Models listed in `think` answer in reasoning
mode, which VeriFact (Chung et al., NEJM AI 2026) found to improve agreement with clinicians.
Each model answers every pending request before the next model is loaded, so the GPU swaps models
once per stage, not once per request.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

_ID = re.compile(r"\bR\d+\b")


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


def _cited_ids(raw, allowed: set[str]) -> list[str]:
    """Supplied ids from a citation field; models sometimes write 'R2: Given heparin' instead of 'R2'."""
    items = raw if isinstance(raw, list) else [raw]
    found = [m for item in items if item for m in _ID.findall(str(item))]
    return [c for c in dict.fromkeys(found) if c in allowed]


class Panel:
    def __init__(self, llm, models: list[str], think: set[str] | None = None):
        self.llm = llm
        self.models = models
        self.think = think or set()
        self.requests: dict[str, Request] = {}

    def submit(self, request: Request) -> None:
        self.requests[request.key] = request

    def _ask(self, model: str, req: Request) -> dict | None:
        user = req.user
        think = model in self.think
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
            for req in self.requests.values():
                req.votes[model] = self._ask(model, req)
            self.llm.unload(model)

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
