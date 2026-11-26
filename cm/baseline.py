"""VeriFact (Chung et al., NEJM AI 2026) applied to this project's ICU cases: retrieval and context.

Follows the VeriFact code (github.com/philipchung/verifact, commit f115d36):
- Every record row is one EHR "fact"; its full text is embedded (VeriFact embeds the fact text; this
  project's own retriever embeds lab and chart rows by their label instead).
- Retrieval methods as in llm_judge/judge_subject.py and reference_context.py:
    dense   top N by bge-m3 dense similarity
    hybrid  top N from dense and top N from sparse, fused with distribution-based score fusion,
            identical texts kept once (highest score), top N kept
    rerank  as hybrid, then every fused candidate is rescored by bge-reranker-v2-m3 and the top N kept
  BM25 stands in for bge-m3 sparse weights, which Ollama does not expose.
- Context in VeriFact's "absolute time" format, oldest first. VeriFact prints the hospital admission
  start and end; this data has no admission table, so the start is the earliest record and the end
  is the decision time (time cut) or the latest record (no cut).
"""

from __future__ import annotations

import datetime as dt

import numpy as np

from .retrieve import Embedder, _dbsf, bm25


class Reranker:
    """bge-reranker-v2-m3 cross-encoder (needs sentence-transformers and torch)."""

    def __init__(self, model: str = "BAAI/bge-reranker-v2-m3"):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise SystemExit("--retrieval-method rerank needs: pip install sentence-transformers torch") from exc
        self.model = CrossEncoder(model, max_length=512)

    def scores(self, query: str, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.predict([(query, t) for t in texts], batch_size=64), dtype=np.float32)


def retrieve(query: str, rows: list[dict], method: str, top_n: int, embedder: Embedder | None,
             reranker: Reranker | None = None) -> list[dict]:
    if not rows:
        return []
    texts = [r["text"] for r in rows]
    dense = embedder.embed(texts) @ embedder.embed([query])[0] if method != "sparse" else None
    if method == "dense":
        order = np.argsort(-dense, kind="stable")[:top_n]
        return [rows[i] for i in order]
    sparse = np.asarray(bm25(query, texts), dtype=np.float32)
    if method == "sparse":
        return [rows[i] for i in np.argsort(-sparse, kind="stable")[:top_n] if sparse[i] > 0]
    pool = list(dict.fromkeys([*np.argsort(-dense, kind="stable")[:top_n],
                               *[i for i in np.argsort(-sparse, kind="stable")[:top_n] if sparse[i] > 0]]))
    fused = _dbsf(dense[pool]) + _dbsf(sparse[pool])
    ranked = [pool[i] for i in np.argsort(-fused, kind="stable")]
    seen, unique = set(), []
    for i in ranked:  # deduplicate_text: keep the first (highest-scoring) copy
        if texts[i] not in seen:
            seen.add(texts[i])
            unique.append(i)
    if method == "rerank":
        if reranker is None:
            raise ValueError("rerank needs a Reranker")
        rs = reranker.scores(query, [texts[i] for i in unique])
        unique = [unique[i] for i in np.argsort(-rs, kind="stable")]
    elif method != "hybrid":
        raise ValueError(f"unknown retrieval method {method!r}")
    return [rows[i] for i in unique[:top_n]]


def _split(stamp: str) -> tuple[str, str]:
    t = (stamp or "").replace("T", " ")
    return (t[:10] or "Unknown"), (t[11:19] if len(t) >= 19 else "Unknown")


def absolute_time_context(facts: list[dict], start: str, end: str) -> str:
    """VeriFact's absolute-time reference context; category = record source, description = record type."""
    out = (f"Hospital Admission Start: {start}\n"
           f"Hospital Admission End: {end}\n"
           "Electronic Health Record Context\n"
           "Ordered by Time (Earliest to Latest):\n")
    for i, f in enumerate(sorted(facts, key=lambda r: r["observed_at"] or ""), 1):
        date, time = _split(f["observed_at"])
        out += (f"{i}. Date: {date}, Time: {time}, Note Category: {f.get('source_type', '')}, "
                f"Note Description: {f.get('semantics', '')} | Text: {f['text']}\n")
    return out


def span(rows: list[dict], end: dt.datetime | None) -> tuple[str, str]:
    times = sorted(r["observed_at"] for r in rows if r.get("observed_at"))
    start = times[0][:19] if times else "None"
    return start, (end.strftime("%Y-%m-%d %H:%M:%S") if end else (times[-1][:19] if times else "None"))
