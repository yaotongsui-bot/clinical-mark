"""Hybrid retrieval of reference facts for one proposition, following VeriFact (Chung et al., NEJM AI 2026).

Dense: bge-m3 embeddings (served by Ollama). Lab and bedside rows are embedded by their item label,
so each distinct label is embedded once; medication, procedure and microbiology rows by their text.
Sparse: BM25 over the full row text, standing in for bge-m3 sparse weights, which Ollama does not
expose. The two score lists are combined with distribution-based score fusion (each normalized to
mean +/- 3 SD, clipped to [0, 1], then summed). The top N rows are returned in chronological order.
VeriFact also reranks with bge-reranker-v2-m3; that model is not available locally, so there is no
rerank step.
"""

from __future__ import annotations

import json
import math
import re
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

ENDPOINT = "http://127.0.0.1:11434"
_STOP = {"the", "a", "an", "of", "with", "for", "to", "is", "are", "was", "and", "or", "in", "on", "at", "be"}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 1]


def bm25(query: str, docs: list[str]) -> list[float]:
    q, toks = tokens(query), [tokens(d) for d in docs]
    n = len(docs) or 1
    avg = sum(len(t) for t in toks) / n or 1.0
    df = Counter(t for doc in toks for t in set(doc))
    scores = []
    for doc in toks:
        tf = Counter(doc)
        scores.append(sum(math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * tf[t] * 2.5 /
                          (tf[t] + 1.5 * (0.25 + 0.75 * len(doc) / avg)) for t in q if t in tf))
    return scores


def dense_text(row: dict) -> str:
    return row["label"] if row.get("table") in {"lab", "chart"} and row.get("label") else row["text"]


class Embedder:
    """bge-m3 vectors with a disk cache (texts.json + vectors.npy, same order)."""

    def __init__(self, cache_dir: Path, model: str = "bge-m3"):
        self.model = model
        self.dir = cache_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.vectors: dict[str, np.ndarray] = {}
        index, store = self.dir / "texts.json", self.dir / "vectors.npy"
        if index.exists() and store.exists():
            texts = json.loads(index.read_text(encoding="utf-8"))
            for text, vec in zip(texts, np.load(store)):
                self.vectors[text] = vec
        self.dirty = False

    def embed(self, texts: list[str]) -> np.ndarray:
        missing = list(dict.fromkeys(t for t in texts if t not in self.vectors))
        for start in range(0, len(missing), 64):
            batch = missing[start:start + 64]
            request = urllib.request.Request(
                ENDPOINT + "/api/embed", headers={"Content-Type": "application/json"},
                data=json.dumps({"model": self.model, "input": batch}).encode("utf-8"))
            with urllib.request.urlopen(request, timeout=600) as response:
                vectors = json.load(response)["embeddings"]
            for text, vec in zip(batch, vectors):
                v = np.asarray(vec, dtype=np.float32)
                self.vectors[text] = v / (np.linalg.norm(v) or 1.0)
            self.dirty = True
        return np.stack([self.vectors[t] for t in texts]) if texts else np.zeros((0, 1024), np.float32)

    def save(self) -> None:
        if not self.dirty:
            return
        texts = list(self.vectors)
        (self.dir / "texts.json").write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
        np.save(self.dir / "vectors.npy", np.stack([self.vectors[t] for t in texts]))
        self.dirty = False


def _dbsf(scores: np.ndarray) -> np.ndarray:
    """Distribution-based score fusion normalization: mean +/- 3 SD mapped to [0, 1]."""
    sd = scores.std()
    if sd == 0:
        return np.zeros_like(scores)
    low, high = scores.mean() - 3 * sd, scores.mean() + 3 * sd
    return np.clip((scores - low) / (high - low), 0, 1)


class Retriever:
    def __init__(self, embedder: Embedder | None, mode: str = "hybrid", top_n: int = 50):
        if mode not in {"hybrid", "dense", "bm25"}:
            raise ValueError(f"unknown retrieval mode {mode!r}")
        if mode != "bm25" and embedder is None:
            raise ValueError("dense or hybrid retrieval needs an embedder")
        self.embedder, self.mode, self.top_n = embedder, mode, top_n

    def search(self, query: str, sparse_query: str, rows: list[dict]) -> list[dict]:
        """query: the proposition (dense); sparse_query: the proposition plus expansion terms (BM25)."""
        if not rows:
            return []
        sparse = np.asarray(bm25(sparse_query, [r["text"] for r in rows]), dtype=np.float32)
        if self.mode == "bm25":
            score = sparse
            keep = [i for i in np.argsort(-score, kind="stable") if score[i] > 0][:self.top_n]
        else:
            dense = self.embedder.embed([dense_text(r) for r in rows]) @ self.embedder.embed([query])[0]
            score = dense if self.mode == "dense" else _dbsf(sparse) + _dbsf(dense)
            keep = list(np.argsort(-score, kind="stable")[:self.top_n])
        return sorted((rows[i] for i in keep), key=lambda r: r["observed_at"])
