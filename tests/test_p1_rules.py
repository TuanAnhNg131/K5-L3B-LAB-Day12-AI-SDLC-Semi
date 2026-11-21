"""Test quy tắc Phase 1 (PRD-0 · Test Contract v1.0) kiểu hộp đen qua headless_cmd."""

import json
import os
import unittest

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


def _tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


class TestGatherRules(unittest.TestCase):
    def test_dive_surface_and_oxygen_drain_refill(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 0.4]}, "random_fish": False}})
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "move": [0, 1]},
                    {"tick": 25, "move": [0, -1]},
                    {"tick": 50, "move": [0, 0]},
                ),
            )
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "60",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            dives = events(rows, "dive")
            surfaces = events(rows, "surface")
            self.assertEqual(len(dives), 1)
            self.assertEqual(len(surfaces), 1)
            self.assertGreater(dives[0]["data"]["pos"][1], 0.5)
            self.assertLessEqual(surfaces[0]["data"]["pos"][1], 0.5)
            last_snap = snapshots(rows)[-1]["player"]
            self.assertEqual(last_snap["oxygen_ticks"], last_snap["oxygen_max_ticks"])
            self.assertEqual(last_snap["zero_oxy_ticks"], 0)

    def test_oxygen_empty_choke_timing_and_surface_save(self):
        # Chạm oxy 0 ở tick 2 -> ngạt lần đầu ở tick 2 + 59 = 61
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {"player": {"pos": [20, 5], "oxygen_ticks": 2}, "random_fish": False}
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "65",
                "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empties = events(rows, "oxygen_empty")
            chokes = events(rows, "choke")
            self.assertEqual([e["tick"] for e in empties], [2])
            self.assertEqual([e["tick"] for e in chokes], [61])
            self.assertEqual(chokes[0]["data"]["hp"], 2)

        # Nổi lên đúng bước đáng lẽ ngạt -> hồi oxy và không ngạt
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 0.52], "vel": [0, -4.0], "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual(len(events(rows, "surface")), 1)
            p = snapshots(rows)[-1]["player"]
            self.assertEqual(p["hp"], 3)
            self.assertEqual(p["oxygen_ticks"], _tuning()["gather"]["oxygen_refill_per_tick"])
            self.assertEqual(p["zero_oxy_ticks"], 0)

    def test_faint_drops_lifo_and_writes_empty_inventory(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                    "hold": ["ca_loc", "bong_sung", "ca_linh"],
                    "random_fish": False,
                }
            })
            inv = w.path("inv.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "10",
                "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "choke")[0]["data"], {"hp": 0})
            faints = events(rows, "faint")
            self.assertEqual(len(faints), 1)
            self.assertEqual(faints[0]["data"], {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
            end_ev = events(rows, "gather_end")[0]["data"]
            self.assertEqual(end_ev, {"reason": "fainted", "inventory": {"items": {}}})
            self.assertEqual(rows[-1]["ticks"], 1)
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_gather_tiebreak_regrow_immediate_and_hold_full(self):
        g = _tuning()["gather"]
        regrow_ticks = int(round(g["regrow_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 0]},
                    "nodes": [
                        {"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                        {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]},
                    ],
                    "hold": ["ca_loc"] * (g["hold_capacity"] - 1),
                    "random_fish": False,
                }
            })
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": 2, "interact": True},
                    {"tick": 3, "interact": False},
                    {"tick": 1 + regrow_ticks, "interact": True},
                ),
            )
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", str(2 + regrow_ticks),
                "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            g_evs = events(rows, "gather")
            self.assertEqual(len(g_evs), 1)
            self.assertEqual(g_evs[0]["tick"], 1)
            self.assertEqual(g_evs[0]["data"], {"node_id": "N2", "kind": "bong_dien_dien", "amount": 1})
            regrown = events(rows, "node_regrown")
            self.assertEqual([e["tick"] for e in regrown], [1 + regrow_ticks])
            full_evs = events(rows, "hold_full")
            # Tick 3 (cố hái N10 khi giỏ đầy) và Tick 2+regrow_ticks (cố hái N2 ngay tick mọc lại khi giỏ đầy)
            self.assertEqual([e["tick"] for e in full_evs], [3, 2 + regrow_ticks])
            self.assertEqual(full_evs[0]["data"], {"action": "gather", "node_id": "N10", "required": 1, "free": 0})
            self.assertEqual(full_evs[1]["data"], {"action": "gather", "node_id": "N2", "required": 1, "free": 0})

    def test_dock_prioritized_over_gather_and_last_tick(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [2, 0]},
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [2.5, 0]}],
                    "time_left_ticks": 1,
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "5",
                "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(rows[-1]["reason"], "docked")

    def test_catch_underwater_cooldown_hold_full_and_final_tick(self):
        g = _tuning()["gather"]
        cd = int(round(g["catch_cooldown_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 5]},
                    "fish": [
                        {"id": "F10", "kind": "ca_loc", "pos": [21, 5]},
                        {"id": "F2", "kind": "ca_linh", "pos": [19, 5]},
                        {"id": "F3", "kind": "ca_loc", "pos": [20.5, 5]},
                    ],
                    "random_fish": False,  # v1.1: tắt cá bơi để giữ nguyên vị trí fixture kiểm cooldown/hold_full
                    "hold": ["bong_sung"] * (g["hold_capacity"] - 3),  # còn đúng 3 ô
                }
            })
            # F3 gần nhất (0.5m, yield 1), sau khi bắt F3 còn 2 ô.
            # Ở tick cd+1 (từ tick 1 -> tick 1+cd): bắt lại, chọn F2 (cách 1.0m == F10 nhưng F2 < F10), yield 3 > free 2 -> hold_full, không thử F10, không đặt cd.
            # Ngay tick tiếp theo di chuyển hoặc giữ nguyên... nếu F2 vẫn gần nhất sẽ lại gặp F2.
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "catch": True},
                    {"tick": 1, "catch": False},
                    {"tick": 5, "catch": True},        # đang hồi chiêu -> bỏ qua
                    {"tick": 6, "catch": False},
                    {"tick": cd, "catch": True},       # tick cd -> frame k=cd -> bước k+1 = 1+cd -> vừa hết cd!
                ),
            )
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", str(cd + 5),
                "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            caught = events(rows, "fish_caught")
            self.assertEqual(len(caught), 1)
            self.assertEqual(caught[0]["tick"], 1)
            self.assertEqual(caught[0]["data"], {"fish_id": "F3", "kind": "ca_loc", "yield": 1})
            fulls = events(rows, "hold_full")
            self.assertEqual(len(fulls), 1)
            self.assertEqual(fulls[0]["tick"], cd + 1)
            self.assertEqual(fulls[0]["data"], {"action": "catch", "fish_id": "F2", "required": 3, "free": 2})
            # F2 và F10 đều vẫn còn, cooldown vẫn bằng 0
            last = snapshots(rows)[-1]
            self.assertEqual([f["id"] for f in last["fish"]], ["F2", "F10"])
            self.assertEqual(last["player"]["catch_cd_ticks"], 0)

        # Bắt ở bước cuối cùng vẫn giữ vào kho khi hết giờ
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 5]},
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 5]}],
                    "time_left_ticks": 1,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            inv = w.path("inv.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "5",
                "--scenario", sc, "--inputs", inp, "--inventory-out", inv, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(len(events(rows, "fish_caught")), 1)
            self.assertEqual(rows[-1]["reason"], "time")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_loc": 1}})


class TestQuanRules(unittest.TestCase):
    def test_customer_schedule_and_no_dish(self):
        # Kho rỗng -> tick 120 phát no_dish; time_left_ticks ngắn vẫn theo phase_tick 120
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {}, "time_left_ticks": 130}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "130", "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            nd = events(rows, "no_dish")
            self.assertEqual([e["tick"] for e in nd], [120])

        # v1.1: 4 bàn (T1..T4). Tick 120 nhận C1 ở T1 (giữ ca_loc); tick 1020 còn bàn T2 nhưng hết nguyên liệu -> phát no_dish
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 1}}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1050", "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], 120)
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [1020])

        # Khi cả 4 bàn đều kín khách -> bỏ lượt ở tick 120 (không phát customer_arrived lẫn no_dish)
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {},
                    "customers": [
                        {"id": f"C{i}", "table_id": f"T{i}", "dish_id": "ca_loc_nuong_trui", "order_status": "unfulfillable"}
                        for i in range(1, 5)
                    ],
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "130", "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "no_dish"), [])

    def test_interact_tiebreak_and_no_fallback(self):
        # B1=[2,8], T1=[2,6]: đặt player tại [2, 6.9] (cách T1 0.9m, B1 1.1m). T1 không có khách, B1 ready -> chọn T1 và bỏ lượt!
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2, 6.9]},
                    "tables": [{"id": "T1", "pos": [2, 6]}],
                    "stoves": [{"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}],
                    "random_customers": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "dish_picked"), [])

        # Đặt player tại [2, 7.0] (cách đều B1 và T1 là 1.0m) -> bếp trước bàn -> nhặt từ B1!
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2, 7.0]},
                    "tables": [{"id": "T1", "pos": [2, 6]}],
                    "stoves": [{"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}],
                    "random_customers": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            picked = events(rows, "dish_picked")
            self.assertEqual(len(picked), 1)
            self.assertEqual(picked[0]["data"]["stove_id"], "B1")

    def test_full_cook_pick_serve_tip_paid_and_ready_ticks(self):
        q = _tuning()["quan"]
        menu = _tuning()["menu"]
        cook_ticks = int(round(menu["lau_ca_linh_dien_dien"]["cook_s"] * 60))
        eat_ticks = int(round(q["eat_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2, 8]},
                    "tables": [{"id": "T1", "pos": [2, 7]}],  # trong tầm nhưng xa hơn B1 (0 vs 1)
                    "stock": {"ca_linh": 3, "bong_dien_dien": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}],
                    "random_customers": False,
                }
            })
            # Tick 0: đứng tại B1 -> interact nấu. Tick 1+cook_ticks: vừa chín (ready_ticks=0).
            # Tick 1+cook_ticks+1: ready_ticks=1 -> nhặt ở tick đó (frame k = cook_ticks+2 -> step k+1 = cook_ticks+3).
            pick_frame = cook_ticks + 2
            serve_frame = cook_ticks + 4
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": pick_frame, "interact": True},
                    {"tick": pick_frame + 1, "move": [0, -1], "interact": False},  # đi sát T1 [2,7]
                    {"tick": serve_frame, "move": [0, 0], "interact": True},
                ),
            )
            # đặt T1 ở [2, 7.6] để không cần đi quá xa; actually move down in 2 ticks at 4m/s only moves little, let's place T1 at [2, 7.8] or just use interact at [2, 7.2]
            # Let's place player at [2, 7.3] so B1 [2,8] is 0.7m (closer!) and T1 [2,6.5] is 0.8m... wait: if B1 is always closer, player never reaches T1 without moving!
            # Instead, move down from [2, 7.3] to [2, 6.7] between pick and serve (takes ~20 ticks).
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2, 7.3]},
                    "tables": [{"id": "T1", "pos": [2, 6.5]}],
                    "stock": {"ca_linh": 3, "bong_dien_dien": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}],
                    "random_customers": False,
                }
            })
            serve_frame = pick_frame + 30
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": pick_frame, "interact": True},
                    {"tick": pick_frame + 1, "move": [0, -1], "interact": False},
                    {"tick": serve_frame, "move": [0, 0], "interact": True},
                ),
            )
            total_ticks = serve_frame + eat_ticks + 5
            code, err = run_headless(
                "--mode", "quan", "--seed", "1", "--ticks", str(total_ticks),
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snaps = {s["tick"]: s for s in snapshots(rows)}

            cs = events(rows, "cook_started")[0]
            self.assertEqual(cs["tick"], 1)
            self.assertEqual(cs["data"]["items"], ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
            self.assertEqual(cs["data"]["base_price"], 120)

            dr = events(rows, "dish_ready")[0]
            self.assertEqual(dr["tick"], 1 + cook_ticks)
            self.assertEqual(snaps[1 + cook_ticks]["stoves"][0]["ready_ticks"], 0)
            self.assertEqual(snaps[2 + cook_ticks]["stoves"][0]["ready_ticks"], 1)

            dp = events(rows, "dish_picked")[0]
            self.assertEqual(dp["tick"], pick_frame + 1)

            sv = events(rows, "served")[0]
            self.assertEqual(sv["tick"], serve_frame + 1)
            self.assertEqual(sv["data"]["base_price"], 120)
            self.assertEqual(sv["data"]["tip"], 24)

            pd = events(rows, "paid")[0]
            self.assertEqual(pd["tick"], serve_frame + 1 + eat_ticks)
            self.assertEqual(pd["data"], {
                "order_id": "C1", "table_id": "T1", "base_price": 120, "tip": 24,
                "amount": 144, "reason": "finished_eating",
            })
            end_row = rows[-1]
            self.assertEqual(end_row["money"], 144)
            self.assertEqual(end_row["earned"], 144)
            self.assertTrue(close(end_row["reputation"], 3.2, 0.001))
            self.assertEqual(end_row["score"], 144 + 300)

    def test_tip_boundary_and_serve_at_zero_patience(self):
        # patience=1801 -> sau bước 1 còn 1800 (đúng 50% của 3600) -> được boa
        # patience=1800 -> sau bước 1 còn 1799 (< 50%) -> boa 0
        for pat_init, want_tip in ((1801, 12), (1800, 0)):
            with Workdir() as w:
                sc = write_json(w.path("sc.json"), {
                    "quan": {
                        "player": {"pos": [9, 2]},
                        "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                        "customers": [{
                            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "order_status": "assigned", "patience_ticks_left": pat_init,
                        }],
                        "random_customers": False,
                    }
                })
                inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
                self.assertEqual(code, 0, err)
                sv = events(read_jsonl(w.path("o.jsonl")), "served")[0]["data"]
                self.assertEqual(sv["tip"], want_tip)

        # Phục vụ đúng tick kiên nhẫn về 0 (ban đầu 1 -> bước 1 giảm còn 0 -> giao thành công)
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [9, 2]},
                    "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "order_status": "assigned", "patience_ticks_left": 1,
                    }],
                    "random_customers": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(len(events(rows, "served")), 1)
            self.assertEqual(events(rows, "customer_left"), [])

    def test_customer_left_patience_clears_stove_and_hand(self):
        # Đang nấu trên bếp -> hết kiên nhẫn bỏ đi, bếp về idle, uy tín -0.5
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 50,
                                "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned", "patience_ticks_left": 1}],
                    "random_customers": False,
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            left = events(rows, "customer_left")[0]["data"]
            self.assertEqual(left["reason"], "patience")
            self.assertTrue(close(left["reputation"], 2.5, 0.001))
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["stoves"][0]["state"], "idle")
            self.assertIsNone(snap["stoves"][0]["dish"])

        # Đang cầm trên tay -> hết kiên nhẫn bỏ đi, tay trống
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned", "patience_ticks_left": 1}],
                    "random_customers": False,
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            snap = snapshots(read_jsonl(w.path("o.jsonl")))[-1]
            self.assertIsNone(snap["hand"])

    def test_closing_tick_behaviors(self):
        # 1) Khách đang chờ hết giờ -> closing, không trừ uy tín, dọn bếp
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "time_left_ticks": 1,
                    "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 50,
                                "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned", "patience_ticks_left": 100}],
                    "random_customers": False,
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            left = events(rows, "customer_left")[0]["data"]
            self.assertEqual(left["reason"], "closing")
            self.assertTrue(close(left["reputation"], 3.0, 0.001))
            qe = events(rows, "quan_end")[0]["data"]
            self.assertEqual(qe["reason"], "time")
            self.assertEqual(rows[-1]["reason"], "time")

        # 2) Vừa giao món đúng tick cuối -> served rồi paid(closing) ngay tick đó
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "time_left_ticks": 1,
                    "player": {"pos": [9, 2]},
                    "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned", "patience_ticks_left": 2500}],
                    "random_customers": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            names = [e["name"] for e in events(rows)]
            self.assertEqual(names, ["served", "paid", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
            self.assertEqual(rows[-1]["earned"], 72)


class TestScenarioValidationAndDeterminism(unittest.TestCase):
    def test_invalid_quan_scenarios_exit_2_without_output(self):
        bad_blocks = [
            # giữ chỗ quá tồn kho
            {"stock": {}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
            # giữ khác công thức
            {"stock": {"ca_loc": 2}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 2}}]},
            # assigned thiếu món ở bếp/tay
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}]},
            # assigned xuất hiện cả ở bếp và tay
            {
                "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                "stoves": [{"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}],
            },
            # món ở bếp không khớp dish_id của khách
            {
                "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 10, "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}}],
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}],
            },
            # eating thiếu giá/tip hoặc eat_ticks_left=0 hoặc order_status != served
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 10}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 0, "base_price": 60, "tip": 0}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "order_status": "reserved", "eat_ticks_left": 10, "base_price": 60, "tip": 0}]},
            # bếp cooking timer = 0 hoặc idle có món
            {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 0, "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
             "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}]},
            {"stoves": [{"id": "B1", "state": "idle", "cook_ticks_left": 5}]},
            # waiting có patience=0
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "unfulfillable", "patience_ticks_left": 0}]},
        ]
        for block in bad_blocks:
            with Workdir() as w:
                sc = write_json(w.path("sc.json"), {"quan": block})
                out = w.path("o.jsonl")
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
                self.assertEqual(code, 2, block)
                self.assertFalse(os.path.exists(out), f"không được ghi out khi lỗi: {block}")

    def test_quan_deterministic_bytes(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 5, "bong_sung": 6, "ca_linh": 6, "bong_dien_dien": 3}}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [-1, 1]}, {"tick": 130, "interact": True}))
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "19", "--ticks", "300", "--scenario", sc, "--inputs", inp, "--out", w.path(f"q{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("q1.jsonl"), "rb") as a, open(w.path("q2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
