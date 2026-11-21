"""Test Phase 4 (TICKET-04 · Test Contract v1.3: bench_cmd, soak_cmd, cảnh báo & tương phản cao)."""

import json
import os
import unittest

from helpers import Workdir, run_contract_cmd


class TestPhase4Release(unittest.TestCase):
    def test_contract_v13_has_bench_and_soak_cmds(self):
        with open("game.contract.json", encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["contract_version"], "1.3")
        self.assertIn("bench_cmd", c)
        self.assertIn("soak_cmd", c)

    def test_bench_cmd_schema_and_bad_args_exit_2(self):
        with Workdir() as w:
            out = w.path("bench.json")
            code, err = run_contract_cmd("bench_cmd", "--seed", "42", "--duration", "0.3", "--warmup", "0.05", "--out", out)
            self.assertEqual(code, 0, err)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data.keys()), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(data["frames"], 0)
            self.assertGreater(data["avg_fps"], 0)
            self.assertGreater(data["p1_low_fps"], 0)
            self.assertGreater(data["measured_s"], 0)
            self.assertGreaterEqual(data["load_ms"], 0)

            bad_out = w.path("bad_bench.json")
            self.assertEqual(run_contract_cmd("bench_cmd", "--seed", "42", "--duration", "0", "--out", bad_out)[0], 2)
            self.assertFalse(os.path.exists(bad_out))

    def test_soak_cmd_10_days_deterministic_and_zero_crashes(self):
        with Workdir() as w:
            s1, s2 = w.path("soak1.json"), w.path("soak2.json")
            for p in (s1, s2):
                code, err = run_contract_cmd("soak_cmd", "--seed", "7", "--days", "10", "--out", p)
                self.assertEqual(code, 0, err)
            with open(s1, encoding="utf-8") as f1, open(s2, encoding="utf-8") as f2:
                d1, d2 = json.load(f1), json.load(f2)
            self.assertEqual(set(d1.keys()), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual(d1["days"], 10)
            self.assertEqual(d1["days_completed"], 10)
            self.assertEqual(d1["crashes"], 0)
            self.assertEqual(len(d1["results"]), 10)
            self.assertEqual([r["day"] for r in d1["results"]], list(range(1, 11)))
            self.assertGreater(d1["results"][-1]["earned"], 0)
            self.assertEqual(d1["results"], d2["results"])

            bad_out = w.path("bad_soak.json")
            self.assertEqual(run_contract_cmd("soak_cmd", "--seed", "7", "--days", "0", "--out", bad_out)[0], 2)
            self.assertFalse(os.path.exists(bad_out))

    def test_ui_accessibility_warnings_high_contrast_and_subtitles(self):
        with open("chonoi/web/index.html", encoding="utf-8") as f:
            html = f.read()
        for token in (
            "high-contrast",
            "toggleHighContrast",
            "THỦY QUÁI GẦN!",
            "OXY SẮP HẾT!",
            "HẾT HƠI",
            "KHÁCH SẮP GIẬN",
            "sfx-subtitle",
        ):
            self.assertIn(token, html)


if __name__ == "__main__":
    unittest.main()
