#!/usr/bin/env bash
# Base answers: Claude's split (reference/split_standard.csv, replayed as model claude-ref) judged by the vote of
# deepseek-v4-pro:0813, minimax-m3.1-flash and glm-5.3 (run.py defaults). Needs OLLAMA_API_KEY.
# Results go to results_final_claude_split/. Judge answers to identical requests replay from the earlier vote.
set -u
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"
DIR=results_final_claude_split
EARLIER=results_final_claude_split_pro_flash_mimo
mkdir -p "$DIR"
[ -f "$DIR/model_cache.jsonl" ] || cp "$EARLIER/model_cache.jsonl" "$DIR/model_cache.jsonl"
rm -rf "$DIR/atoms" "$DIR/cases"
"$PY" -B run.py --triples input/mimic_triples_deepseek.json --out-dir "$DIR" --ai-model claude-ref > "$DIR.log" 2>&1
echo "$DIR exit $?"
