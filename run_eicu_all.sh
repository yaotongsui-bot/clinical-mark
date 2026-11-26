#!/usr/bin/env bash
# Test-set runs on the eICU demo (PAPER_PLAN.md). Every system judges the same fact atoms (the
# evaluator's split, made once per answer set in ours_vote of the first run). Outputs stay unscored
# until the test reference is written and frozen.
#
#   bash run_eicu_all.sh cloud GENERATOR...   evaluator with the cloud vote and with deepseek-v4-pro;
#                                             VeriFact with deepseek-v4-pro (needs OLLAMA_API_KEY)
#   bash run_eicu_all.sh local GENERATOR...   evaluator (full and all-to-judge) and VeriFact (records cut
#                                             at T, and as published) with llama3.1:8b
#   bash run_eicu_all.sh factehr GENERATOR... FactEHR entailment judge with deepseek-v4-pro, whole record
#                                             before T as premise (run_factehr.py; needs OLLAMA_API_KEY)
#
# GENERATOR is the suffix of input/eicu_triples_<GENERATOR>.json, e.g. gpt-oss-120b.
# Environment (all optional):
#   RESULTS     output root (default results_eicu)
#   ATOMS_FROM  root whose <G>/ours_vote holds the atoms to judge (default RESULTS; set it for a rerun so
#               the atoms are not split again)
#   CACHE_FROM  root whose <G>/<run>/model_cache.jsonl seeds each new run (requests that did not change
#               are answered from it; the cache is keyed by the exact request)
#   EMB, EMBVF  embedding caches (cache only; results do not depend on them). Give jobs that run at the
#               same time their own copies: each process rewrites the whole cache when it saves.
set -u
cd "$(dirname "$0")"
PY="${PYTHON:-python}"
PHASE=$1; shift
PRO=deepseek-v4-pro:0813:cloud
LLAMA=llama3.1:8b-instruct-q4_K_M
R="${RESULTS:-results_eicu}"
A="${ATOMS_FROM:-$R}"
C="${CACHE_FROM:-}"
EMB="${EMB:-embeddings_eicu}"
EMBVF="${EMBVF:-embeddings_eicu_vf}"

prepare() {  # prepare G RUN WITH_ATOMS: atoms from the first split, seed cache
  mkdir -p "$R/$1/$2"
  if [ "$3" = atoms ] && [ "$A/$1/ours_vote" != "$R/$1/$2" ]; then cp -r "$A/$1/ours_vote/atoms" "$R/$1/$2/"; fi
  if [ -n "$C" ] && [ -f "$C/$1/$2/model_cache.jsonl" ] && [ ! -f "$R/$1/$2/model_cache.jsonl" ]; then
    cp "$C/$1/$2/model_cache.jsonl" "$R/$1/$2/"
  fi
}

finished() {  # run.py writes summary.json at the end, run_baseline85.py writes verdicts.csv
  [ -f "$1/summary.json" ] || [ -f "$1/verdicts.csv" ]
}

ours() {  # ours G RUN [run.py options]
  local G=$1 RUN=$2; shift 2
  if finished "$R/$G/$RUN"; then echo "$G $RUN already finished"; return; fi
  prepare "$G" "$RUN" atoms
  "$PY" -B run.py --source eicu --triples "input/eicu_triples_$G.json" --out-dir "$R/$G/$RUN" --labels verifact \
    --embeddings-dir "$EMB" "$@" > "$R/$G/$RUN.log" 2>&1
  echo "$G $RUN exit $?"
}

verifact() {  # verifact G RUN JUDGE TIMECUT
  local G=$1 RUN=$2
  if finished "$R/$G/$RUN"; then echo "$G $RUN already finished"; return; fi
  prepare "$G" "$RUN" none
  "$PY" -B run_baseline85.py --source eicu --triples "input/eicu_triples_$G.json" --atoms "$A/$G/ours_vote" \
    --time-cut "$4" --judge-model "$3" --out-dir "$R/$G/$RUN" --embeddings-dir "$EMBVF" > "$R/$G/$RUN.log" 2>&1
  echo "$G $RUN exit $?"
}

factehr() {  # factehr G RUN JUDGE
  local G=$1 RUN=$2
  if finished "$R/$G/$RUN"; then echo "$G $RUN already finished"; return; fi
  prepare "$G" "$RUN" none
  "$PY" -B run_factehr.py --source eicu --triples "input/eicu_triples_$G.json" --atoms "$A/$G/ours_vote" \
    --judge-model "$3" --out-dir "$R/$G/$RUN" > "$R/$G/$RUN.log" 2>&1
  echo "$G $RUN exit $?"
}

for G in "$@"; do
  mkdir -p "$R/$G"
  if [ "$PHASE" = cloud ]; then
    ours "$G" ours_vote
    ours "$G" ours_pro --judge-models "$PRO"
    verifact "$G" vf_pro_cut "$PRO" before
  elif [ "$PHASE" = local ]; then
    ours "$G" ours_llama --judge-models "$LLAMA"
    ours "$G" ours_llama_alljudge --judge-models "$LLAMA" --facts-all-judge
    verifact "$G" vf_llama_cut "$LLAMA" before
    verifact "$G" vf_llama_nocut "$LLAMA" none
  elif [ "$PHASE" = factehr ]; then
    factehr "$G" fe_pro_cut "$PRO"
  else
    echo "usage: bash run_eicu_all.sh cloud|local|factehr GENERATOR..." >&2
    exit 2
  fi
done
