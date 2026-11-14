"""Reader for the PhysioNet release MIMIC-III-Ext-VeriFact-BHC v1.1.0 (Chung et al., NEJM AI 2026).

The file names and columns follow the release adapter and replay script in the VeriFact repository
(github.com/philipchung/verifact, MIT: scripts/analysis_verifact/release_data.py and
scripts/evaluate/replay_physionet_v1_1_0.py):

  propositions/propositions.csv.gz      proposition_id, text, subject_id, author_type (llm | human),
                                        proposition_type (claim | sentence)
  propositions/human_verdicts.csv.gz    proposition_id, text, author_type, proposition_type, human_gt
  verifact/verdicts.parquet             model, proposition_id, rater_alias, reference_id, verdict, reason, ...
  verifact/rater_configurations.csv     model, rater_alias, rater_name, fact_type, retrieval_method, top_n,
                                        reference_format, reference_only_admission, deduplicate_text
  verifact/reference_payloads.parquet   reference_id, reference (the context text the judge saw)
  verifact/model_metadata.csv, verifact/model_configuration_matrix.csv
  reference_ehr/ehr_noteevents.csv.gz   the reference EHR notes (columns not documented; see cm/notes.py)

The release is MIMIC-III credentialed data: it must stay out of the public repository and must not be
sent to hosted model APIs (the MIMIC data use agreement). See check_local_models().
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

DEFAULT_RELATIVE = Path("data") / "physionet.org" / "files" / "mimic-iii-ext-verifact-bhc" / "1.1.0"
LABELS = ("supported", "not_supported", "not_addressed")
# VeriFact's verdict strings and this project's labels.
TO_VERIFACT = {"supported": "Supported", "not_supported": "Not Supported", "not_addressed": "Not Addressed"}
# The configuration the paper reports as best: hybrid retrieval with reranking, 50 facts, whole EHR.
BEST = {"retrieval_method": "rerank", "top_n": "50", "reference_format": "absolute_time",
        "reference_only_admission": "false"}


def release_dir(given: Path | None, project_root: Path) -> Path:
    """--release-dir, else VERIFACTBHC_DATASET_DIR, else the path a PhysioNet wget download creates."""
    if given:
        return given.resolve()
    env = os.environ.get("VERIFACTBHC_DATASET_DIR", "").strip()
    return Path(env).resolve() if env else (project_root / DEFAULT_RELATIVE).resolve()


def _file(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.exists():
        raise FileNotFoundError(f"release file missing: {path}")
    return path


def norm_label(value) -> str | None:
    """'Supported', 'Not Supported', 'not_addressed', 'NOT ADDRESSED' -> this project's label."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    key = str(value).strip().lower().replace("-", " ").replace("_", " ")
    key = " ".join(key.split())
    return {"supported": "supported", "not supported": "not_supported",
            "not addressed": "not_addressed"}.get(key)


def _text(value) -> str:
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value).strip().lower()


def load_propositions(root: Path) -> pd.DataFrame:
    df = pd.read_csv(_file(root, "propositions/propositions.csv.gz"), dtype=str, keep_default_na=False,
                     usecols=["proposition_id", "text", "subject_id", "author_type", "proposition_type"])
    if df["proposition_id"].duplicated().any():
        raise ValueError("propositions.csv.gz has duplicate proposition_id")
    return df


def load_ground_truth(root: Path) -> pd.DataFrame:
    """proposition_id -> human_gt as this project's label. Unknown strings stop the run."""
    df = pd.read_csv(_file(root, "propositions/human_verdicts.csv.gz"), dtype=str, keep_default_na=False)
    df["label"] = df["human_gt"].map(norm_label)
    unknown = sorted(set(df.loc[df["label"].isna(), "human_gt"]))
    if unknown:
        raise ValueError(f"human_verdicts.csv.gz has labels this reader does not know: {unknown[:10]}")
    if df["proposition_id"].duplicated().any():
        raise ValueError("human_verdicts.csv.gz has duplicate proposition_id")
    return df[["proposition_id", "label", "human_gt"]]


def load_rater_configurations(root: Path) -> pd.DataFrame:
    df = pd.read_csv(_file(root, "verifact/rater_configurations.csv"), dtype=str, keep_default_na=False)
    for col in ("retrieval_method", "reference_format", "reference_only_admission", "fact_type"):
        if col in df:
            df[col] = df[col].map(_text).str.replace(" ", "_")
    return df


def select_raters(configs: pd.DataFrame, model: str, fact_type: str | None = None, **params: str) -> pd.DataFrame:
    """Rater configurations of one released model that match the given settings (strings, lower case).

    With fact_type None every fact type is kept (VeriFact matches it to the proposition type).
    """
    keep = configs["model"] == model
    for col, value in {**BEST, **params}.items():
        if value is not None:
            keep &= configs[col].astype(str).str.lower() == str(value).lower()
    if fact_type:
        keep &= configs["fact_type"] == fact_type
    out = configs[keep]
    if out.empty:
        models = sorted(configs["model"].unique())
        raise ValueError(f"no rater configuration for model={model} {params or BEST}; models: {models}")
    return out


def load_verdicts(root: Path, model: str, rater_aliases: list[str] | None = None) -> pd.DataFrame:
    """Released VeriFact verdicts of one model (optionally some rater aliases), with label added."""
    filters = [("model", "==", model)]
    if rater_aliases:
        filters.append(("rater_alias", "in", list(rater_aliases)))
    df = pd.read_parquet(_file(root, "verifact/verdicts.parquet"), filters=filters,
                         columns=["model", "proposition_id", "rater_alias", "reference_id", "verdict"])
    df["label"] = df["verdict"].map(norm_label)
    return df


def load_references(root: Path, reference_ids: set[str]) -> dict[str, str]:
    """reference_id -> reference text, read in batches so the whole file is never in memory."""
    import pyarrow.parquet as pq

    wanted, out = {str(r) for r in reference_ids}, {}
    for batch in pq.ParquetFile(_file(root, "verifact/reference_payloads.parquet")).iter_batches(
            columns=["reference_id", "reference"], batch_size=2048):
        for rid, ref in zip(batch.column(0).to_pylist(), batch.column(1).to_pylist()):
            if str(rid) in wanted:
                out[str(rid)] = ref
    missing = wanted - set(out)
    if missing:
        raise ValueError(f"{len(missing)} reference_id values are not in reference_payloads.parquet")
    return out


def check_local_models(models: list[str]) -> None:
    """The data use agreement does not allow sending MIMIC-III text to a hosted API."""
    from urllib.parse import urlparse

    from .llm import ENDPOINT

    hosted = [m for m in models if m.endswith(":cloud")]
    if hosted:
        raise SystemExit(f"VeriFact-BHC is MIMIC-III credentialed data; hosted models are not allowed: {hosted}")
    host = urlparse(ENDPOINT).hostname or ""
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit(f"VeriFact-BHC needs a local Ollama; CLINICAL_MARK_OLLAMA_ENDPOINT points to {host}")
