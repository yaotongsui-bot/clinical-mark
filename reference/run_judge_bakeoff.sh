#!/usr/bin/env bash
# Judge-only comparison: every model judges the same atoms (deepseek-v4-pro:0813's split, replayed from its cache).
# Needs OLLAMA_API_KEY. Results go to results_bakeoff/<model>.
set -u
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"
SPLIT_MODEL="deepseek-v4-pro:0813:cloud"
SOURCE=results_models/deepseek-v4-pro_0813/model_cache.jsonl
run() {
  local model="$1" lane="$2"
  local dir="results_bakeoff/${model//:/_}"
  mkdir -p "$dir"
  [ -f "$dir/model_cache.jsonl" ] || grep '"stage": "ai_atomization"' "$SOURCE" > "$dir/model_cache.jsonl"
  "$PY" -B run.py --triples input/mimic_triples_deepseek.json --out-dir "$dir" --ai-model "$SPLIT_MODEL" \
    --judge-models "$model:cloud" --judge-think "" --embeddings-dir "$lane" > "$dir.log" 2>&1
  echo "$model exit $?"
}
run deepseek-v4-pro:0813 embeddings &
run kimi-k3.1-pro embeddings_lane2 &
run deepseek-v4.1-flash embeddings_lane3 &
run mimo-v2.6-pro embeddings_lane4 &
wait
