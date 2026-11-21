"""Benchmark có render 1280x720 cho cảnh lặn buổi sáng (TICKET-04, Test Contract v1.3).

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
"""

import time

_T_BOOT = time.perf_counter()

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402

from .contract import load_contract  # noqa: E402
from .errors import BadInput  # noqa: E402
from .inputs import InputState  # noqa: E402
from .runner import Session  # noqa: E402

W = 1280
H = 720
ROW_STRIDE = W * 3
TICK_S = 1.0 / 60.0

KIND_RGB = {
    "ca_loc": (122, 158, 82),
    "ca_linh": (201, 232, 255),
    "ca_keo": (224, 157, 85),
    "bong_dien_dien": (242, 194, 48),
    "bong_sung": (239, 125, 163),
    "keo_neo": (130, 207, 99),
}


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


def _pos_float(name):
    def conv(s):
        try:
            v = float(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số")
        if not math.isfinite(v) or v <= 0:
            raise argparse.ArgumentTypeError(f"{name} phải > 0")
        return v
    return conv


def _nonneg_float(name):
    def conv(s):
        try:
            v = float(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số")
        if not math.isfinite(v) or v < 0:
            raise argparse.ArgumentTypeError(f"{name} phải >= 0")
        return v
    return conv


def _fill_rect(buf: bytearray, x0: int, y0: int, w: int, h: int, rgb: tuple):
    x1 = min(W, x0 + w)
    y1 = min(H, y0 + h)
    x0 = max(0, x0)
    y0 = max(0, y0)
    if x1 <= x0 or y1 <= y0:
        return
    cw = x1 - x0
    row_bytes = bytes(rgb) * cw
    off0 = x0 * 3
    off1 = x1 * 3
    for y in range(y0, y1):
        base = y * ROW_STRIDE
        buf[base + off0:base + off1] = row_bytes


def _build_background(gather_tuning: dict) -> bytearray:
    bg = bytearray(W * H * 3)
    top = 80
    oy = 175
    bottom = H - 64
    # Thanh HUD trên và dưới
    _fill_rect(bg, 0, 0, W, top, (15, 27, 36))
    _fill_rect(bg, 0, bottom, W, H - bottom, (15, 27, 36))
    # Bầu trời bình minh
    for y in range(top, oy):
        t = (y - top) / max(1, oy - top)
        rgb = (int(255 - 64 * t), int(216 + 13 * t), int(184 + 61 * t))
        _fill_rect(bg, 0, y, W, 1, rgb)
    # Nước phù sa chuyển sâu
    for y in range(oy, bottom):
        t = (y - oy) / max(1, bottom - oy)
        rgb = (int(92 - 81 * t), int(157 - 126 * t), int(178 - 130 * t))
        _fill_rect(bg, 0, y, W, 1, rgb)
    # Đường mặt nước
    _fill_rect(bg, 0, oy, W, 3, (233, 247, 255))
    # Bến nhà sàn
    dp = gather_tuning["dock_pos"]
    sx = int(20 + (dp[0] / 100.0) * (W - 40))
    _fill_rect(bg, max(0, sx - 22), oy - 16, 44, 16, (141, 98, 59))
    _fill_rect(bg, max(0, sx - 26), oy - 32, 52, 16, (184, 74, 50))
    return bg


def _render_frame(bg: bytearray, snap: dict, gather_tuning: dict) -> bytearray:
    buf = bytearray(bg)
    oy = 175
    bottom = H - 64
    water_h = bottom - oy
    bounds = gather_tuning["bounds"]
    x_max = float(bounds["x"][1])
    d_max = float(bounds["d"][1])

    def to_px(pos):
        return (int(20 + (pos[0] / x_max) * (W - 40)), int(oy + (pos[1] / d_max) * water_h))

    # Nút hái
    for n in snap["nodes"]:
        nx, ny = to_px(n["pos"])
        col = KIND_RGB.get(n["kind"], (200, 200, 200))
        _fill_rect(buf, nx - 10, ny - 6, 20, 12, col)

    # Đàn cá
    for f in snap["fish"]:
        fx, fy = to_px(f["pos"])
        col = KIND_RGB.get(f["kind"], (210, 210, 210))
        _fill_rect(buf, fx - 12, fy - 6, 24, 12, col)

    # Cá Sấu Năm Chèo
    for m in snap["monsters"]:
        mx, my = to_px(m["pos"])
        col = (229, 57, 53) if m["state"] == "chase" else ((144, 164, 174) if m["state"] == "recoil" else (75, 123, 62))
        _fill_rect(buf, mx - 20, my - 8, 40, 16, col)

    # Út Sen & HUD
    p = snap["player"]
    px, py = to_px(p["pos"])
    _fill_rect(buf, px - 9, py - 9, 18, 18, (91, 59, 110))
    _fill_rect(buf, px - 4, py - 7, 8, 5, (38, 198, 218))

    # Thanh oxy & máu
    oxy_w = int(220 * (p["oxygen_ticks"] / max(1, p["oxygen_max_ticks"])))
    _fill_rect(buf, 120, 24, 220, 22, (20, 30, 38))
    _fill_rect(buf, 120, 24, oxy_w, 22, (79, 195, 247))
    for i in range(p["hp_max"]):
        _fill_rect(buf, 360 + i * 28, 24, 20, 20, (255, 107, 129) if i < p["hp"] else (60, 70, 80))

    # Thanh giỏ dưới
    for i in range(snap["hold_capacity"]):
        _fill_rect(buf, 20 + i * 36, H - 48, 28, 28, (45, 58, 68))
    for i, it in enumerate(snap["hold"]):
        col = KIND_RGB.get(it["kind"], (200, 200, 200))
        _fill_rect(buf, 23 + i * 36, H - 45, 22, 22, col)

    return buf


def run_benchmark(seed: int, duration_s: float, warmup_s: float, out_path: str) -> dict:
    contract = load_contract()
    tuning = contract["tuning"]
    gather_t = tuning["gather"]
    bg = _build_background(gather_t)
    sess = Session("gather", tuning, {}, seed)
    idle_inp = InputState((0.0, 0.0), {"interact": False, "catch": False, "pause": False, "shop_done": False}, set())

    # Khung hình đầu tiên -> đo load_ms
    snap = sess.snapshot()
    _render_frame(bg, snap, gather_t)
    load_ms = round((time.perf_counter() - _T_BOOT) * 1000.0, 2)

    acc = 0.0
    last_t = time.perf_counter()
    warmup_end = last_t + warmup_s
    while time.perf_counter() < warmup_end:
        now = time.perf_counter()
        acc += now - last_t
        last_t = now
        while acc >= TICK_S:
            if sess.done:
                sess = Session("gather", tuning, {}, seed)
            sess.step(idle_inp)
            acc -= TICK_S
        _render_frame(bg, sess.snapshot(), gather_t)

    frame_dts = []
    meas_start = time.perf_counter()
    meas_end = meas_start + duration_s
    last_t = meas_start
    while True:
        f_start = time.perf_counter()
        if f_start >= meas_end and frame_dts:
            break
        acc += f_start - last_t
        last_t = f_start
        while acc >= TICK_S:
            if sess.done:
                sess = Session("gather", tuning, {}, seed)
            sess.step(idle_inp)
            acc -= TICK_S
        _render_frame(bg, sess.snapshot(), gather_t)
        f_end = time.perf_counter()
        frame_dts.append(max(1e-6, f_end - f_start))
        if f_end >= meas_end:
            break

    measured_s = max(1e-6, time.perf_counter() - meas_start)
    frames = len(frame_dts)
    avg_fps = round(frames / measured_s, 2)
    slow_k = max(1, math.ceil(0.01 * frames))
    slowest = sorted(frame_dts, reverse=True)[:slow_k]
    p1_low_fps = round(1.0 / (sum(slowest) / slow_k), 2)

    result = {
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
        "frames": frames,
        "measured_s": round(measured_s, 4),
        "load_ms": load_ms,
    }

    abs_out = os.path.abspath(out_path)
    out_dir = os.path.dirname(abs_out)
    fd, tmp = tempfile.mkstemp(prefix=".bench-", suffix=".tmp", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, abs_out)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return result


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.bench")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--duration", required=True, type=_pos_float("duration"))
    p.add_argument("--warmup", type=_nonneg_float("warmup"), default=3.0)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if not os.path.isdir(os.path.dirname(os.path.abspath(a.out))):
            raise BadInput(f"thư mục đầu ra không tồn tại: {a.out}")
        run_benchmark(a.seed, a.duration, a.warmup, a.out)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
