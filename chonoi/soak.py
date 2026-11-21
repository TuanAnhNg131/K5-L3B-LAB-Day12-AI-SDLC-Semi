"""Soak headless nhiều Ngày liên tục bằng bot tất định (TICKET-04, Test Contract v1.3).

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def _dir_vec(src, dst):
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    n = math.hypot(dx, dy)
    if n <= 1e-6:
        return (0.0, 0.0)
    return (dx / n, dy / n)


class DeterministicBot:
    """Bot tất định chơi xuyên gather -> quan -> shop mà không dùng RNG ngoài hay đồng hồ."""

    def __init__(self, tuning):
        self.tuning = tuning
        self._toggle = 0

    def next_input(self, snap: dict) -> InputState:
        self._toggle ^= 1
        ph = snap["phase"]
        edges = set()
        buy = None
        mv = (0.0, 0.0)

        if ph == "gather":
            mv, edges = self._step_gather(snap)
        elif ph == "quan":
            mv, edges = self._step_quan(snap)
        elif ph == "shop":
            buy, edges = self._step_shop(snap)

        held = {b: (b in edges) for b in ("interact", "catch", "pause", "shop_done")}
        return InputState(mv, held, edges, buy=buy)

    def _step_gather(self, snap: dict):
        p = snap["player"]
        pos = p["pos"]
        g = self.tuning["gather"]
        edges = set()
        oxy_ratio = p["oxygen_ticks"] / max(1, p["oxygen_max_ticks"])
        need_surface = oxy_ratio < 0.35 or (not p["at_surface"] and oxy_ratio < 0.8)

        # Kiểm tra về bến nếu đủ hàng, gần hết giờ hoặc ít máu
        should_dock = (
            len(snap["hold"]) >= 5
            or snap["phase_tick"] >= 1800
            or p["hp"] <= 1
            or snap["time_left_ticks"] <= 1500
        )
        if should_dock:
            if math.dist(pos, g["dock_pos"]) <= g["dock_radius"]:
                if self._toggle:
                    edges.add("interact")
                return (0.0, 0.0), edges
            return _dir_vec(pos, [g["dock_pos"][0], 0.0]), edges

        if need_surface and not p["at_surface"]:
            return (0.0, -1.0), edges

        # Tìm nguyên liệu còn thiếu trong kế hoạch ngày
        needed = dict(snap["day_plan"]["ingredients"])
        for it in snap["hold"]:
            if it["fresh"] >= self.tuning["freshness"]["spoiled_below"] and needed.get(it["kind"], 0) > 0:
                needed[it["kind"]] -= 1

        ready_nodes = [n for n in snap["nodes"] if n["ready"]]
        want_nodes = [n for n in ready_nodes if needed.get(n["kind"], 0) > 0] or ready_nodes
        want_fish = [f for f in snap["fish"] if needed.get(f["kind"], 0) > 0] or snap["fish"]

        # Ưu tiên bắt cá gần trên đường hoặc hái nút trên mặt nước
        if want_fish and oxy_ratio >= 0.55 and p["hp"] >= 2:
            tgt_f = min(want_fish, key=lambda f: math.dist(pos, f["pos"]))
            if math.dist(pos, tgt_f["pos"]) <= g["catch_radius"] and not p["at_surface"] and p["catch_cd_ticks"] == 0:
                if self._toggle:
                    edges.add("catch")
                return (0.0, 0.0), edges
            if not want_nodes or math.dist(pos, tgt_f["pos"]) < 15.0:
                return _dir_vec(pos, tgt_f["pos"]), edges

        if want_nodes:
            tgt_n = min(want_nodes, key=lambda n: math.dist(pos, n["pos"]))
            if math.dist(pos, tgt_n["pos"]) <= g["interact_radius"] and p["at_surface"]:
                if self._toggle:
                    edges.add("interact")
                return (0.0, 0.0), edges
            return _dir_vec(pos, [tgt_n["pos"][0], 0.0]), edges

        return _dir_vec(pos, g["dock_pos"]), edges

    def _step_quan(self, snap: dict):
        pos = snap["player"]["pos"]
        rad = self.tuning["quan"]["interact_radius"]
        edges = set()
        hand = snap["hand"]

        if hand is not None:
            cust = next((c for c in snap["customers"] if c["id"] == hand["order_id"]), None)
            if cust:
                tb = next(t for t in snap["tables"] if t["id"] == cust["table_id"])
                if math.dist(pos, tb["pos"]) <= rad:
                    if self._toggle:
                        edges.add("interact")
                    return (0.0, 0.0), edges
                return _dir_vec(pos, tb["pos"]), edges

        ready_stoves = [s for s in snap["stoves"] if s["state"] == "ready"]
        if ready_stoves and hand is None:
            st = min(ready_stoves, key=lambda s: math.dist(pos, s["pos"]))
            if math.dist(pos, st["pos"]) <= rad:
                if self._toggle:
                    edges.add("interact")
                return (0.0, 0.0), edges
            return _dir_vec(pos, st["pos"]), edges

        reserved = [c for c in snap["customers"] if c["state"] == "waiting" and c["order_status"] == "reserved"]
        idle_stoves = [s for s in snap["stoves"] if s["state"] == "idle"]
        if reserved and idle_stoves:
            st = min(idle_stoves, key=lambda s: math.dist(pos, s["pos"]))
            if math.dist(pos, st["pos"]) <= rad:
                if self._toggle:
                    edges.add("interact")
                return (0.0, 0.0), edges
            return _dir_vec(pos, st["pos"]), edges

        return _dir_vec(pos, [3.5, 7.5]), edges

    def _step_shop(self, snap: dict):
        edges = set()
        buy = None
        if snap["phase_tick"] == 0:
            upgs = self.tuning["shop"]["upgrades"]
            cur = snap["upgrades"]
            money = snap["money"]
            for kind in ("oxygen", "hp"):
                lvl = cur.get(kind, 0)
                nxt = next((u for u in upgs[kind] if u["level"] == lvl + 1), None)
                if nxt and money >= nxt["price"]:
                    buy = kind
                    break
        else:
            edges.add("shop_done")
        return buy, edges


def run_soak(seed: int, days: int, out_path: str) -> dict:
    t0 = time.perf_counter()
    tuning = load_contract()["tuning"]
    mult = tuning["score"]["reputation_multiplier"]
    sess = Session("day", tuning, {}, seed, days=days)
    sess.init_events()
    bot = DeterministicBot(tuning)

    results = []
    crashes = 0
    max_ticks = days * 23_000
    try:
        while not sess.done and sess.tick < max_ticks:
            snap = sess.snapshot()
            inp = bot.next_input(snap)
            ev_rows, _ = sess.step_detail(inp)
            for ev in ev_rows:
                if ev["name"] == "shop_end":
                    sim = sess.sim
                    results.append({
                        "day": ev["day"],
                        "earned": sim.earned,
                        "reputation": round(sim.reputation, 3),
                        "score": sim.earned + mult * math.floor(sim.reputation),
                    })
    except Exception:
        crashes += 1

    payload = {
        "days": days,
        "days_completed": sess.sim.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": round(time.perf_counter() - t0, 3),
    }

    abs_out = os.path.abspath(out_path)
    out_dir = os.path.dirname(abs_out)
    fd, tmp = tempfile.mkstemp(prefix=".soak-", suffix=".tmp", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, abs_out)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return payload


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--days", required=True, type=_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if a.days < 1:
            raise BadInput("--days phải >= 1")
        if not os.path.isdir(os.path.dirname(os.path.abspath(a.out))):
            raise BadInput(f"thư mục đầu ra không tồn tại: {a.out}")
        res = run_soak(a.seed, a.days, a.out)
        if res["crashes"] > 0:
            return 1
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
