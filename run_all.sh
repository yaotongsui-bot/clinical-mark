#!/usr/bin/env bash
# Rebuild every result in this folder. Model answers are kept in each <out-dir>/model_cache.jsonl, so with
# the shipped caches this replays in minutes; with empty caches it needs Ollama and several hours.
# These are the local-model runs, so their models are named here; run.py's own default is now the cloud model.
# The fact judge and atomizer prompts changed on 2026-11-06, so answers cached before that date are requested again.
# Usage: bash run_all.sh
set -u
cd "$(dirname "$0")"
PY="${PYTHON:-python}"
MIMIC="data/mimic-iv-demo"
export PYTHONIOENCODING=utf-8
"$PY" -m unittest discover tests || { echo "### regression tests failed"; exit 1; }

run() {
  echo "### $(date +%H:%M:%S) evaluate $2"
  rm -rf "$2/atoms" "$2/cases"
  "$PY" run.py --triples "$1" --mimic-root "$MIMIC" --out-dir "$2" --ai-model qwen2.5:14b \
    --judge-models gemma4:12b,llama3.1:8b-instruct-q4_K_M,qwen2.5:14b --judge-think gemma4:12b \
    | grep -E --line-buffered "atomize (20|40|60|85)/|judge panel|Traceback|Error"
  echo "### $2 exit=${PIPESTATUS[0]}"
}

run input/mimic_triples_fixed.json results_fixed
# Never overwrite an annotation set: it may already hold clinician labels.
[ -d annotation_set ] || "$PY" make_annotation_set.py results_fixed --triples input/mimic_triples_fixed.json \
  --mimic-root "$MIMIC" --cases 20 --out annotation_set
run input/mimic_triples_fixed.json validation/retest_fixed
"$PY" stability_compare.py results_fixed validation/retest_fixed validation/stability_results_fixed.md > /dev/null
run input/mimic_frozen_triples.json results
"$PY" compare_runs.py results results_fixed --out results_fixed/comparison.md > /dev/null
"$PY" sensitivity.py results_fixed --triples input/mimic_triples_fixed.json --mimic-root "$MIMIC" --out validation/sensitivity_fixed
for k in 1 2 3; do run "input/mimic_triples_open_s$k.json" "results_open_s$k"; done
"$PY" summarize_samples.py results_open_s1 results_open_s2 results_open_s3 --baseline results_fixed --out results_open_summary.md > /dev/null
"$PY" make_controls.py > /dev/null
for k in error_injection doctor_as_ai; do run "input/control_$k.json" "validation/controls/$k"; done
"$PY" score_controls.py > /dev/null
echo "### $(date +%H:%M:%S) ALL DONE"
