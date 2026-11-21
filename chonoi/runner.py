"""Vòng tick (Contract B, mô hình tick v1.1).

Thứ tự ghi: các event tick 0 (nếu có) -> snapshot tick 0 -> với mỗi bước: event rồi snapshot
(khi tới lượt, đổi pha, hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.
"""

import math
import os
import tempfile

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, max_days=days)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, xử lý pause, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _event_row(self, tick, phase, name, data, day=None):
        row = {"type": "event", "tick": tick, "phase": phase}
        if self.mode == "day":
            row["day"] = day
        row["name"] = name
        row["data"] = data
        return row

    def init_events(self) -> list:
        if hasattr(self.sim, "pop_init_events"):
            return [self._event_row(0, ph, nm, dt, day=d) for ph, d, nm, dt in self.sim.pop_init_events()]
        return []

    def snapshot(self) -> dict:
        state = "finished" if self.sim.done else ("paused" if self.paused else "playing")
        s = _common(self.sim, self.tick, self.sim_tick, self.sim.phase_tick, self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def step_detail(self, inp) -> tuple:
        """Chạy một bước với `inp`; trả (danh sách dòng event, phase_changed)."""
        self.tick += 1
        pause_edge = inp.pressed("pause")
        rows = []
        cur_day = getattr(self.sim, "day", None)

        if not self.paused and pause_edge:
            self.paused = True
            rows.append(self._event_row(self.tick, self.sim.phase, "paused", {}, day=cur_day))
            return rows, False

        if self.paused:
            if not pause_edge:
                return rows, False
            self.paused = False
            rows.append(self._event_row(self.tick, self.sim.phase, "resumed", {}, day=cur_day))

        self.sim_tick += 1
        if self.mode == "day":
            events, phase_changed = self.sim.step(inp)
            for ph, d, nm, dt in events:
                rows.append(self._event_row(self.tick, ph, nm, dt, day=d))
            return rows, phase_changed

        for nm, dt in self.sim.step(inp):
            rows.append(self._event_row(self.tick, self.sim.phase, nm, dt))
        return rows, False

    def step(self, inp) -> list:
        """Giữ tương thích API P1: chỉ trả danh sách dòng event."""
        rows, _ = self.step_detail(inp)
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        state = "finished" if sim.done else ("paused" if self.paused else "playing")
        score = _common(sim, self.tick, self.sim_tick, sim.phase_tick, self.tuning, state)["score"]
        row = {
            "type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
            "state": state,
            "reason": sim.reason if sim.done else "tick_limit",
            "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score,
        }
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames)
    abs_out = os.path.abspath(out_path)
    out_dir = os.path.dirname(abs_out)
    use_tmp = (not os.path.exists(abs_out)) or os.path.isfile(abs_out)
    tmp_path = None
    if use_tmp:
        fd, tmp_path = tempfile.mkstemp(prefix=".out-", suffix=".tmp", dir=out_dir)
        os.close(fd)
        target_path = tmp_path
    else:
        target_path = out_path
    w = JsonlWriter(target_path)
    try:
        for row in sess.init_events():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            ev_rows, phase_changed = sess.step_detail(inp)
            for row in ev_rows:
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or phase_changed:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
        w.close()
        if use_tmp:
            os.replace(tmp_path, abs_out)
            tmp_path = None
    except BaseException:
        try:
            w.close()
        except Exception:
            pass
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
