# Frozen deepseek answers

Frozen on 2026-11-03. These answer files are the fixed input for every deepseek evaluation from now on. The answers are not regenerated; evaluation reruns read them as they are. The files are set read-only, so `generate_answers.py` cannot overwrite them by accident.

Answers came from `deepseek-v4.1-flash:cloud` (think off) through `generate_answers.py --model`. 85 of the 100 cases have an answer: those whose decision time falls inside the ICU stay.

| File | Variant | Temperature | Seed | Cases answered | Claims | Bytes |
|---|---|---|---|---|---|---|
| mimic_triples_deepseek.json | up to 3 actions | 0.0 | 20260925 | 85 | 255 | 28333363 |
| mimic_triples_open_deepseek_s1.json | up to 10 actions | 0.7 | 20260925 | 85 | 850 | 28482304 |
| mimic_triples_open_deepseek_s2.json | up to 10 actions | 0.7 | 20260926 | 85 | 850 | 28484332 |
| mimic_triples_open_deepseek_s3.json | up to 10 actions | 0.7 | 20260927 | 85 | 850 | 28486197 |

Each file has a matching `*_generation_raw.jsonl` holding the model's raw replies, which are frozen too. The open-sample files carry a `generation` block copied from the first run, so their `total_claims` (299) and reuse counts are stale. The table above has the correct counts.

To regenerate on purpose, clear the read-only flag first and write to new file names. Don't overwrite these files.
