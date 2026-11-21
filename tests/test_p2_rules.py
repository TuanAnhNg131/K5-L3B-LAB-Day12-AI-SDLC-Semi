"""Test quy tắc Phase 2 (TICKET-02 · Test Contract v1.1) kiểu hộp đen và live."""

import json
import os
import time
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


def _tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


class TestGatherV11(unittest.TestCase):
    def test_v11_new_ingredients_nodes_and_fish(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [76, 0]},
                    "random_fish": False,
                    "monsters": [],
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "200",
                "--scenario", sc, "--inputs", inp, "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            sn0 = snapshots(rows)[0]
            self.assertEqual([n["id"] for n in sn0["nodes"]], ["N1", "N2", "N3", "N4", "N5", "N6"])
            self.assertEqual(events(rows, "gather")[0]["data"]["kind"], "keo_neo")

        # Bắt ca_keo thu yield 2
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [30, 24]},
                    "fish": [{"id": "F1", "kind": "ca_keo", "pos": [30, 24]}],
                    "random_fish": False,
                    "monsters": [],
                    "time_left_ticks": 1,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            inv = w.path("inv.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "5",
                "--scenario", sc, "--inputs", inp, "--inventory-out", inv, "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            self.assertEqual(events(rows, "fish_caught")[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_keo": 2}})

    def test_fish_initial_swim_corner_reflect_turn_and_spawn(self):
        # Kiểm tra 8 đàn ban đầu ở 8 điểm riêng, và sinh đàn thứ 9 ở tick 360
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"monsters": []}})
            code, err = run_headless(
                "--mode", "gather", "--seed", "5", "--ticks", "360",
                "--scenario", sc, "--snapshot-every", "360", "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            snaps = snapshots(rows)
            pts0 = {tuple(f["pos"]) for f in snaps[0]["fish"]}
            self.assertEqual(len(snaps[0]["fish"]), 8)
            self.assertEqual(len(pts0), 8)
            spawned = events(rows, "fish_spawned")
            self.assertEqual([e["tick"] for e in spawned], [360])
            self.assertEqual(len(snaps[-1]["fish"]), 9)

        # Kiểm tra phản xạ góc (96, 28) hướng 45 độ -> đảo cả x và d thành 225 độ
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "fish": [{"id": "F1", "kind": "ca_keo", "pos": [95.99, 27.99], "heading_deg": 45}],
                    "monsters": [],
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--snapshot-every", "1", "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            f1 = snapshots(read_jsonl(w.path("g.jsonl")))[-1]["fish"][0]
            self.assertLess(f1["pos"][0], 96.0)
            self.assertLess(f1["pos"][1], 28.0)
            self.assertTrue(close(f1["heading_deg"], 225.0, 0.5), f1)

        # Kiểm tra đổi hướng ở bước bơi thứ 120 (age_ticks 119 -> 120)
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 7], "heading_deg": 0, "age_ticks": 119}],
                    "monsters": [],
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "3", "--ticks", "1",
                "--scenario", sc, "--snapshot-every", "1", "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            f1 = snapshots(read_jsonl(w.path("g.jsonl")))[-1]["fish"][0]
            self.assertEqual(f1["age_ticks"], 120)
            self.assertNotEqual(f1["heading_deg"], 0)

    def test_monster_patrol_chase_hit_recoil_invuln_and_choke_pierce(self):
        # Tuần tra đến waypoint rồi quay đầu, phát hiện chase khi d>=10 và <=10m, đánh rớt floor(len/2) LIFO, recoil 60 tick
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [60, 24]},
                    "hold": ["ca_loc", "bong_sung", "ca_keo"],
                    "random_fish": False,
                    "monsters": [{
                        "id": "M1", "kind": "ca_sau", "pos": [60, 24],
                        "waypoints": [[60, 24], [64, 24]], "target_idx": 1,
                    }],
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "62",
                "--scenario", sc, "--snapshot-every", "1", "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            hits = events(rows, "monster_hit")
            # Hit tại tick 1 (trùng tâm dùng +x để recoil), không hit suốt invuln/recoil 60 tick
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["tick"], 1)
            self.assertEqual(hits[0]["data"], {
                "monster_id": "M1", "hp": 2, "lost": ["ca_keo"], "pos": [60.0, 24.0],
            })
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[1]["hold"], ["ca_loc", "bong_sung"])
            self.assertEqual(snaps[1]["player"]["invuln_ticks"], 90)
            self.assertEqual(snaps[1]["monsters"][0]["state"], "recoil")
            self.assertEqual(snaps[1]["monsters"][0]["recoil_dir"], [1.0, 0.0])
            # Tick 61: xong recoil bước thứ 60 -> về patrol, chưa hit; Tick 62: vẫn đang invuln
            self.assertEqual(snaps[61]["monsters"][0]["state"], "patrol")
            self.assertIsNone(snaps[61]["monsters"][0]["recoil_dir"])
            self.assertGreater(snaps[61]["monsters"][0]["pos"][0], 61.9)

        # Ngạt xuyên bất tử và không làm rơi hàng (trừ khi ngất)
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 10], "hp": 3, "oxygen_ticks": 0, "zero_oxy_ticks": 59, "invuln_ticks": 50},
                    "hold": ["ca_loc", "bong_sung"],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            self.assertEqual(events(rows, "choke")[0]["data"], {"hp": 2})
            self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_loc", "bong_sung"])

    def test_monster_faint_in_day_mode_delivers_empty_and_day3_m2(self):
        # Đánh chết -> faint cause="monster", liệt kê giỏ còn lại theo LIFO, sang quán với kho rỗng
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [60, 24], "hp": 1},
                    "hold": ["ca_loc", "bong_sung", "ca_linh"],
                    "random_fish": False,
                    "monsters": [{
                        "id": "M1", "kind": "ca_sau", "pos": [60, 24],
                        "waypoints": [[60, 24], [64, 24]],
                    }],
                },
                "quan": {"random_customers": False},
            })
            code, err = run_headless("--mode", "day", "--days", "1", "--seed", "1", "--ticks", "2", "--scenario", sc, "--out", w.path("d.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            self.assertEqual(events(rows, "monster_hit")[0]["data"]["lost"], ["ca_linh"])
            self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "monster", "lost": ["bong_sung", "ca_loc"], "hp": 0})
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": {}})
            sn1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual(sn1["phase"], "quan")
            self.assertEqual(sn1["phase_tick"], 0)
            self.assertEqual(sn1["stock"], {})


class TestDayShopPauseAndValidationV11(unittest.TestCase):
    def test_day_2_days_plan_filtering_shop_buy_and_next_day_upgrades(self):
        # Kiểm tra Day 1 -> Day 2, buy + shop_done cùng bước, upgrades có hiệu lực từ Ngày 2, Ngày 3 có M2
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "day": {"money": 250, "earned": 250},
                "gather": {
                    "player": {"pos": [2, 0]},
                    "hold": ["ca_loc", "ca_keo", "ca_keo"],  # ca_keo không thuộc D1 plan -> quán D1 chỉ chọn ca_loc_nuong_trui
                    "random_fish": False,
                    "time_left_ticks": 60,
                },
                "quan": {"time_left_ticks": 150},
            })
            # Tick 0: dock ngay -> tick 1 vào quan. Tick 121: khách đến gọi ca_loc_nuong_trui.
            # Tick 151: quan kết thúc -> vào shop D1.
            # Tick 152 (frame 152): buy="unknown" -> buy_failed.
            # Tick 153 (frame 153): buy="oxygen" (200k) và shop_done=True cùng lúc -> bought trước rồi shop_end("done") -> sang Day 2!
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": 152, "buy": "bad_item"},
                    {"tick": 153, "buy": "oxygen", "shop_done": True},
                ),
            )
            code, err = run_headless(
                "--mode", "day", "--days", "2", "--seed", "7", "--ticks", "200",
                "--scenario", sc, "--inputs", inp, "--out", w.path("d.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))

            # Tick 0 init events
            t0_evs = [e for e in events(rows) if e["tick"] == 0]
            self.assertEqual([(e["name"], e["day"], e["phase"]) for e in t0_evs], [
                ("day_start", 1, "gather"),
                ("day_plan", 1, "gather"),
                ("phase_start", 1, "gather"),
            ])

            # Trong quán Ngày 1 chỉ được gọi món thuộc D1 plan (ca_loc_nuong_trui, không gọi ca_keo_nuong dù có ca_keo!)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["data"]["dish_id"], "ca_loc_nuong_trui")

            # Shop events
            bf = events(rows, "buy_failed")[0]
            self.assertEqual(bf["data"], {"action": "bad_item", "reason": "unknown"})
            bt = events(rows, "bought")[0]
            self.assertEqual(bt["tick"], 154)
            self.assertEqual(bt["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 50})
            se = events(rows, "shop_end")[0]
            self.assertEqual(se["tick"], 154)
            self.assertEqual(se["data"], {"reason": "done"})

            # Snapshot ngay sau khi đóng shop Ngày 1 -> Ngày 2 gather với active_upgrades.oxygen == 1 (2700 oxy)
            sn_d2 = [s for s in snapshots(rows) if s["tick"] == 154][0]
            self.assertEqual(sn_d2["day"], 2)
            self.assertEqual(sn_d2["phase"], "gather")
            self.assertEqual(sn_d2["phase_tick"], 0)
            self.assertEqual(sn_d2["money"], 50)
            self.assertEqual(sn_d2["earned"], 250)
            self.assertEqual(sn_d2["upgrades"], {"oxygen": 1})
            self.assertEqual(sn_d2["active_upgrades"], {"oxygen": 1})
            self.assertEqual(sn_d2["player"]["oxygen_max_ticks"], 2700)

    def test_shop_auto_close_max_days_and_day3_monster(self):
        # Shop tự đóng sau 600 tick -> shop_end("time") và kết thúc ngày 3 có M1 + M2
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {"player": {"pos": [2, 0]}, "random_fish": False},
                "quan": {"time_left_ticks": 60, "random_customers": False},
            })
            # Lịch trình 3 ngày với time_left_ticks=60 ở quan và shop max 600
            # Day 1: dock tick 0->1, quan 60 tick (61), shop 600 tick (661) -> sang Day 2
            # Day 2: dock tick 661->662, quan 60 (722), shop 600 (1322) -> sang Day 3!
            # Day 3: dock tick 1322->1323, quan 60 (1383), shop 600 (1983) -> days_complete!
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": 661, "interact": True},
                    {"tick": 662, "interact": False},
                    {"tick": 1322, "interact": True},
                    {"tick": 1323, "interact": False},
                ),
            )
            code, err = run_headless(
                "--mode", "day", "--days", "3", "--seed", "1", "--ticks", "2500",
                "--scenario", sc, "--inputs", inp, "--out", w.path("d.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            end_row = rows[-1]
            self.assertEqual(end_row["reason"], "days_complete")
            self.assertEqual(end_row["days_completed"], 3)
            self.assertEqual([e["data"]["reason"] for e in events(rows, "shop_end")], ["time", "time", "time"])
            sn_d3 = [s for s in snapshots(rows) if s.get("day") == 3 and s["phase"] == "gather"][0]
            self.assertEqual([m["id"] for m in sn_d3["monsters"]], ["M1", "M2"])

    def test_pause_freezes_timers_and_ignores_actions(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 5]}, "random_fish": False, "monsters": []}})
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "pause": True},                       # tick 1: vào pause
                    {"tick": 1, "pause": False, "move": [1, 0]},     # bị bỏ qua khi pause
                    {"tick": 5, "pause": True},                       # tick 6: resumed và chạy gameplay ngay bước đó
                ),
            )
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "6",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            self.assertEqual(events(rows, "paused")[0]["tick"], 1)
            self.assertEqual(events(rows, "resumed")[0]["tick"], 6)
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[1]["state"], "paused")
            self.assertEqual(snaps[1]["sim_tick"], 0)
            self.assertEqual(snaps[5]["sim_tick"], 0)
            self.assertEqual(snaps[5]["player"]["oxygen_ticks"], 1800)
            # Tick 6 resumed và chạy 1 bước gameplay
            self.assertEqual(snaps[6]["state"], "playing")
            self.assertEqual(snaps[6]["sim_tick"], 1)
            self.assertEqual(snaps[6]["player"]["oxygen_ticks"], 1799)

    def test_day_scenarios_exit_2_without_output(self):
        bad_scenarios = [
            {"day": {"money": 100}},  # thiếu earned
            {"day": {"money": 200, "earned": 100}},  # money > earned
            {"day": {"upgrades": {"oxygen": 3}}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 2}}]}},
            {"quan": {"stock": {"ca_loc": 1}}},
            {"quan": {"reputation": 4.0}},
            {"gather": {"monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "state": "recoil", "state_ticks_left": 0, "recoil_dir": [1, 0]}]}},
            {"gather": {"monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "state": "recoil", "state_ticks_left": 5, "recoil_dir": [2, 0]}]}},
            # Món trong quan.customers không nằm trong kế hoạch D1 (lỗi khi mở quán)
            {"gather": {"player": {"pos": [2, 0]}, "hold": ["ca_keo", "ca_keo"], "random_fish": False},
             "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong"}]}},
        ]
        for idx, sc_obj in enumerate(bad_scenarios):
            with Workdir() as w:
                sc = write_json(w.path("sc.json"), sc_obj)
                inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
                out = w.path("d.jsonl")
                code, _ = run_headless("--mode", "day", "--days", "1", "--seed", "1", "--ticks", "5", "--scenario", sc, "--inputs", inp, "--out", out)
                self.assertEqual(code, 2, (idx, sc_obj))
                self.assertFalse(os.path.exists(out), (idx, "không được để lại file output khi mã 2"))

    def test_day_performance_and_determinism(self):
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}))
            t0 = time.perf_counter()
            for i in (1, 2):
                code, err = run_headless(
                    "--mode", "day", "--days", "1", "--seed", "42", "--ticks", "22200",
                    "--inputs", inp, "--out", w.path(f"d{i}.jsonl"),
                )
                self.assertEqual(code, 0, err)
            dt = time.perf_counter() - t0
            self.assertLess(dt, 40.0)  # 2 lần chạy < 40s (1 lần < 20s)
            rows = read_jsonl(w.path("d1.jsonl"))
            self.assertEqual(rows[-1]["reason"], "days_complete")
            self.assertEqual(rows[-1]["days_completed"], 1)
            with open(w.path("d1.jsonl"), "rb") as a, open(w.path("d2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())

    def test_live_day_mode_server(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("day", tuning, {}, 1, days=2), port=0)
        server.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{server.port}/state", timeout=5) as r:
                st = json.loads(r.read())
            self.assertEqual(st["mode"], "day")
            self.assertEqual(st["phase"], "gather")
            self.assertEqual(st["day"], 1)
            self.assertEqual(st["max_days"], 2)
            self.assertIn("day_plan", st)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
