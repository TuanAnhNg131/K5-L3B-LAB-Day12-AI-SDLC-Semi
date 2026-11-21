"""Test quy tắc Phase 3 (TICKET-03 · Test Contract v1.2 — Độ tươi & kho cá thể)."""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestFreshnessAndSpoilage(unittest.TestCase):
    def test_gather_spoiled_threshold_sample_from_spec(self):
        # Đúng ví dụ kiểm ngưỡng trong TICKET-03: fresh=30 ươn ngay ở tick 1 và chỉ phát 1 lần
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc, "--snapshot-every", "1", "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            sp = events(rows, "spoiled")
            self.assertEqual(len(sp), 1)
            self.assertEqual(sp[0], {"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                                     "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}})
            # Hàng ươn vẫn chiếm ô giỏ
            self.assertEqual(len(snapshots(rows)[-1]["hold"]), 1)

    def test_multi_item_spoiled_order_pause_and_quan_exact_threshold(self):
        # Nhiều cá thể cùng vượt ngưỡng 30 -> phát theo id_key (I2 trước I10)
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [
                        {"id": "I10", "kind": "ca_loc", "fresh": 30},
                        {"id": "I2", "kind": "bong_sung", "fresh": 30},
                    ],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            sp = events(read_jsonl(w.path("g.jsonl")), "spoiled")
            self.assertEqual([e["data"]["item_id"] for e in sp], ["I2", "I10"])

        # Ở quán (0.25/s = 1/240 tick): bắt đầu tại 30 + 1/240 -> tick 1 vừa chạm 30 (chưa ươn), tick 2 -> ươn!
        # Đồng thời kiểm pause dừng hao tươi
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 30 + 1 / 240}],
                    "random_customers": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 1, "pause": True}, {"tick": 2, "pause": False}, {"tick": 5, "pause": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "6", "--scenario", sc, "--inputs", inp, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("q.jsonl"))
            sp = events(rows, "spoiled")
            # Tick 1: không pause, 30+1/240 -> 30 (chưa ươn). Tick 2..5: pause. Tick 6: resumed và hao 30 -> <30 (ươn tại tick 6!)
            self.assertEqual([(e["tick"], e["data"]["location"]) for e in sp], [(6, "stock")])

    def test_file_handoff_preserves_exact_freshness_threshold(self):
        # Gather với fresh = 30 + 3/240, cập bến ở tick 0 (hao 2/240 -> còn 30 + 1/240), xuất file kho sang quan:
        # sang quan tick 1 giảm còn 30 (chưa ươn), tick 2 mới phát spoiled!
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 30 + 3 / 240}],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "5", "--scenario", sc, "--inputs", inp, "--inventory-out", inv, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "2", "--inventory", inv, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            sp = events(read_jsonl(w.path("q.jsonl")), "spoiled")
            self.assertEqual([e["tick"] for e in sp], [2])


class TestReservationAndPricingV12(unittest.TestCase):
    def test_reserve_freshest_tiebreak_id_and_rereserve_cascade_on_spoilage(self):
        # Đơn C1 (T1, order_tick 0): giữ I1 (ca_linh 30 -> ươn ở tick 1), I2 (ca_linh 90), I3 (ca_linh 90), I4 (bong_dien_dien 80).
        # Đơn C2 (T2, order_tick 0): giữ I5 (ca_loc 90), I6 (bong_dien_dien 30 -> ươn ở tick 1).
        # Không có thêm ca_linh hay bong_dien_dien dự phòng!
        # Tick 1: I1 và I6 cùng ươn -> C1 xử lý trước (T1 < T2): nhả I1,I2,I3,I4, không đủ 3 ca_linh -> unfulfillable (I4 được giải phóng!).
        # Tiếp đó C2 xử lý: nhả I5,I6 và giữ lại được I5 (tươi) + I4 (vừa được C1 nhả)!
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": [
                        {"id": "I1", "kind": "ca_linh", "fresh": 30},
                        {"id": "I2", "kind": "ca_linh", "fresh": 90},
                        {"id": "I3", "kind": "ca_linh", "fresh": 90},
                        {"id": "I4", "kind": "bong_dien_dien", "fresh": 80},
                        {"id": "I5", "kind": "ca_loc", "fresh": 90},
                        {"id": "I6", "kind": "bong_dien_dien", "fresh": 30},
                    ],
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien", "order_tick": 0, "reserved": ["I1", "I2", "I3", "I4"]},
                        {"id": "C2", "table_id": "T2", "dish_id": "canh_chua_ca_loc", "order_tick": 0, "reserved": ["I5", "I6"]},
                    ],
                    "random_customers": False,
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", sc, "--snapshot-every", "1", "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("q.jsonl"))
            self.assertEqual([e["data"]["item_id"] for e in events(rows, "spoiled")], ["I1", "I6"])
            custs = {c["id"]: c for c in snapshots(rows)[-1]["customers"]}
            self.assertEqual(custs["C1"]["order_status"], "unfulfillable")
            self.assertEqual(custs["C1"]["reserved"], [])
            self.assertEqual(custs["C2"]["order_status"], "reserved")
            self.assertEqual(custs["C2"]["reserved"], ["I4", "I5"])

    def test_freshest_selection_tiebreak_price_floor_and_cooked_no_decay(self):
        # Kiểm chọn tươi nhất hòa lấy id nhỏ (I10 tươi 80, I2 tươi 80, I1 tươi 50 -> tự cấp lấy I2, không lấy I10 hay I1)
        # Và chốt giá floor(40 * (79.995833... + 89.995833...) / 2 / 100) = floor(40 * 84.995833 / 100) = floor(33.99833) = 33
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2, 7.3]},
                    "tables": [{"id": "T1", "pos": [2, 6.5]}],
                    "stock": [
                        {"id": "I1", "kind": "bong_sung", "fresh": 50},
                        {"id": "I10", "kind": "bong_sung", "fresh": 80},
                        {"id": "I2", "kind": "bong_sung", "fresh": 80},
                        {"id": "I3", "kind": "bong_sung", "fresh": 90},
                    ],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}],  # không khai reserved -> tự chọn I3 (90) và I2 (80, I2 < I10)
                    "random_customers": False,
                }
            })
            # Kiểm snapshot tick 0 đã cấp ["I2", "I3"], sau đó interact tick 0 nấu -> pick ở tick 242 -> serve ở tick 272 -> paid ở 872
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 242, "interact": True},
                {"tick": 243, "move": [0, -1], "interact": False},
                {"tick": 272, "move": [0, 0], "interact": True},
            ))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "900", "--scenario", sc, "--inputs", inp, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("q.jsonl"))
            sn0 = snapshots(rows)[0]
            self.assertEqual(sn0["customers"][0]["reserved"], ["I2", "I3"])
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual([x["id"] for x in cs["items"]], ["I2", "I3"])
            self.assertEqual(cs["base_price"], 33)
            # Món chín không hao thêm dù nấu 240 tick và giữ trên bếp/tay -> tip = floor(33 * 0.2) = 6
            pd = events(rows, "paid")[0]["data"]
            self.assertEqual(pd["base_price"], 33)
            self.assertEqual(pd["tip"], 6)
            self.assertEqual(pd["amount"], 39)

    def test_day_continuous_ids_no_transition_or_shop_decay(self):
        # Day 1: hold có I2, hái N1 gần [12,0] -> cấp I3! Không hao thêm khi chuyển sang quan hay trong shop;
        # Sang Day 2: mẫu hold được cấp id mới nối tiếp (I4), không đụng I2/I3.
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [12, 0]},
                    "hold": [{"id": "I2", "kind": "ca_loc", "fresh": 100}],
                    "random_fish": False,
                    "monsters": [],
                    "time_left_ticks": 3,
                },
                "quan": {"time_left_ticks": 2, "random_customers": False},
            })
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},  # tick 1: hái N1 -> tạo I3 (fresh 100)
                {"tick": 1, "interact": False},
                {"tick": 6, "shop_done": True},  # tick 5 vào shop, tick 6 giữ nguyên độ tươi trong shop, tick 7 đóng shop -> sang Day 2
            ))
            code, err = run_headless("--mode", "day", "--days", "2", "--seed", "1", "--ticks", "10", "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", w.path("d.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            snaps = {s["tick"]: s for s in snapshots(rows)}
            # Tick 1: hái I3 (fresh 100), I2 đã hao 1 tick
            self.assertEqual([(x["id"], x["fresh"]) for x in snaps[1]["hold"]], [("I2", 99.992), ("I3", 100)])
            # Tick 3: gather kết thúc (time) -> chuyển sang quan cùng tick 3, không hao thêm tại bước chuyển pha
            self.assertEqual(snaps[3]["phase"], "quan")
            self.assertEqual([(x["id"], x["fresh"]) for x in snaps[3]["stock"]], [("I2", 99.975), ("I3", 99.983)])
            # Tick 5 vào shop, tick 6 trong shop không hao độ tươi
            self.assertEqual(snaps[5]["phase"], "shop")
            self.assertEqual(snaps[6]["phase"], "shop")
            self.assertEqual(snaps[6]["stock"], snaps[5]["stock"])
            # Day 2 tick 7: mẫu hold nhận id mới I4!
            self.assertEqual(snaps[7]["day"], 2)
            self.assertEqual(snaps[7]["hold"], [{"id": "I4", "kind": "ca_loc", "fresh": 100}])

    def test_v12_invalid_scenarios_exit_2_without_output(self):
        bad_list = [
            ("gather", {"gather": {"hold": ["ca_loc"]}}),
            ("quan", {"quan": {"stock": {"ca_loc": 1}}}),
            ("quan", {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 80}]}}),
            ("quan", {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 29}], "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]}}),
            ("quan", {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 90}], "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 1}}]}}),
            ("quan", {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 90}],
                               "customers": [
                                   {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                                   {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                               ]}}),
        ]
        for mode, sc_obj in bad_list:
            with Workdir() as w:
                sc = write_json(w.path("sc.json"), sc_obj)
                out = w.path("o.jsonl")
                code, _ = run_headless("--mode", mode, "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
                self.assertEqual(code, 2, (mode, sc_obj))
                self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
