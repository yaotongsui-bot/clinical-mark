"""Repeat runs: seed shift and cache key (cm/llm.py). No model calls. Run:  python -m unittest tests.test_repeat"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cm import llm  # noqa: E402


class Sent(Exception):
    pass


class RepeatSampling(unittest.TestCase):
    def test_first_repeat_leaves_requests_unchanged(self):
        self.assertIsNone(llm.repeat_sampling(None, 1))
        self.assertEqual(llm.repeat_sampling({"temperature": 0.1, "seed": llm.SEED + 2}, 1),
                         {"temperature": 0.1, "seed": llm.SEED + 2})

    def test_later_repeats_shift_the_seed_only(self):
        self.assertEqual(llm.repeat_sampling(None, 2), {"seed": llm.SEED + 1000})
        self.assertEqual(llm.repeat_sampling({"temperature": 0.1, "seed": llm.SEED + 2}, 3),
                         {"temperature": 0.1, "seed": llm.SEED + 2002})

    def test_repeat_asks_again_instead_of_using_the_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model_cache.jsonl"
            record = {"request": ["m", "s", "u", {}], "response": {"label": "Supported"}}
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            saved = llm.REPEAT
            try:
                llm.REPEAT = 1
                cache = llm.LLM(path)
                self.assertEqual(cache.json("m", "s", "u", {}), {"label": "Supported"})
                llm.REPEAT = 2
                cache = llm.LLM(path)
                sent = []

                def post(_path, payload, **_kw):
                    sent.append(payload)
                    raise Sent

                cache._post = post
                with self.assertRaises(Sent):
                    cache.json("m", "s", "u", {})
                self.assertEqual(sent[0]["options"]["seed"], llm.SEED + 1000)
                self.assertEqual(sent[0]["options"]["temperature"], 0)
            finally:
                llm.REPEAT = saved


if __name__ == "__main__":
    unittest.main()
