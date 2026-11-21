"""Nạp và kiểm scenario (Contract D / v1.1). Trả về dict chuẩn hóa theo mode."""

import copy
import json
import math

from .errors import BadInput
from .inventory import KINDS_V11, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
GATHER_NODE_KEYS = {"id", "kind", "pos", "regrow_ticks"}
GATHER_FISH_KEYS = {"id", "kind", "pos", "heading_deg", "age_ticks"}
GATHER_MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")

QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
QUAN_TABLE_KEYS = {"id", "pos"}
QUAN_CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                      "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
DISH_PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}

DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài miền ({axis} ∈ [{lo}, {hi}])")


def _apply_day_upgrades(tuning, upgrades):
    t = copy.deepcopy(tuning)
    shop_upgs = t["shop"]["upgrades"]
    if upgrades.get("oxygen", 0) > 0:
        for item in shop_upgs["oxygen"]:
            if item["level"] == upgrades["oxygen"]:
                t["gather"]["oxygen_max_s"] = item["oxygen_max_s"]
                break
    if upgrades.get("hp", 0) > 0:
        for item in shop_upgs["hp"]:
            if item["level"] == upgrades["hp"]:
                t["gather"]["hp_max"] = item["hp_max"]
                break
    return t


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")

    if mode == "day":
        allowed_top = {"day", "gather", "quan"}
        extra_top = set(data) - allowed_top
        if extra_top:
            raise BadInput(f"scenario cho --mode day chỉ nhận {sorted(allowed_top)}, gặp {sorted(extra_top)}")
        eff_tuning = tuning
        if "day" in data:
            day_block = data["day"]
            if not isinstance(day_block, dict):
                raise BadInput("khối day phải là object")
            _validate_day(day_block, tuning)
            if "upgrades" in day_block:
                eff_tuning = _apply_day_upgrades(tuning, day_block["upgrades"])
        if "gather" in data:
            gblock = data["gather"]
            _check_block_common("gather", gblock, eff_tuning)
            _validate_gather(gblock, eff_tuning)
        if "quan" in data:
            qblock = data["quan"]
            _check_block_common("quan", qblock, eff_tuning)
            if "stock" in qblock or "reputation" in qblock:
                raise BadInput("chế độ day không nhận quan.stock hoặc quan.reputation")
            _validate_quan(qblock, eff_tuning)
        return data

    if not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    _check_block_common(mode, block, tuning)
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _check_block_common(mode, block, tuning):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")


def _validate_day(d, tuning):
    extra = set(d) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ trong day: {sorted(extra)}")
    if ("money" in d) != ("earned" in d):
        raise BadInput("day phải khai cả money và earned khi có tiền đầu kỳ")
    if "money" in d:
        _nonneg_int("day.money", d["money"])
        _nonneg_int("day.earned", d["earned"])
        if d["money"] > d["earned"]:
            raise BadInput("day.money không được vượt day.earned")
    q = tuning["quan"]
    if "reputation" in d:
        rep = d["reputation"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput("day.reputation phải nằm trong [reputation_min, reputation_max]")
    if "upgrades" in d:
        upgs = d["upgrades"]
        if not isinstance(upgs, dict):
            raise BadInput("day.upgrades phải là object")
        shop_upgs = tuning["shop"]["upgrades"]
        for k, v in upgs.items():
            if k not in shop_upgs:
                raise BadInput(f"day.upgrades: nâng cấp lạ {k}")
            max_lvl = len(shop_upgs[k])
            if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v <= max_lvl):
                raise BadInput(f"day.upgrades.{k} phải thuộc [0, {max_lvl}]")
    if "day_plan" in d:
        plans = d["day_plan"]
        if not isinstance(plans, list):
            raise BadInput("day.day_plan phải là mảng")
        seen_days = set()
        menu = tuning["menu"]
        for pl in plans:
            if not isinstance(pl, dict):
                raise BadInput("day.day_plan: phần tử phải là object")
            extra_p = set(pl) - {"day", "dishes", "ingredients"}
            if extra_p:
                raise BadInput(f"day.day_plan: trường lạ {sorted(extra_p)}")
            day_num = pl.get("day")
            if isinstance(day_num, bool) or not isinstance(day_num, int) or not (1 <= day_num <= 5) or day_num in seen_days:
                raise BadInput("day.day_plan: day phải nguyên duy nhất trong [1, 5]")
            seen_days.add(day_num)
            dishes = pl.get("dishes")
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput(f"day.day_plan ngày {day_num}: dishes phải là object khác rỗng")
            calc = {}
            for did, cnt in dishes.items():
                if did not in menu or isinstance(cnt, bool) or not isinstance(cnt, int) or cnt <= 0:
                    raise BadInput(f"day.day_plan ngày {day_num}: món {did!r} không hợp lệ")
                for k, qty in menu[did]["recipe"].items():
                    calc[k] = calc.get(k, 0) + qty * cnt
            if "ingredients" in pl:
                ings = validate_items(pl["ingredients"])
                if ings != calc:
                    raise BadInput(f"day.day_plan ngày {day_num}: ingredients không khớp tổng công thức")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS_V11 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        max_zero = int(g["choke_interval_ticks"]) - 1
        if p["zero_oxy_ticks"] > max_zero:
            raise BadInput(f"player.zero_oxy_ticks phải trong [0, {max_zero}]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        extra_n = set(n) - GATHER_NODE_KEYS
        if extra_n:
            raise BadInput(f"nodes.{n['id']}: trường lạ {sorted(extra_n)}")
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        extra_f = set(f) - GATHER_FISH_KEYS
        if extra_f:
            raise BadInput(f"fish.{f['id']}: trường lạ {sorted(extra_f)}")
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    species = g["monsters"]["species"]
    for m in b.get("monsters", []):
        extra_m = set(m) - GATHER_MONSTER_KEYS
        if extra_m:
            raise BadInput(f"monsters.{m['id']}: trường lạ {sorted(extra_m)}")
        kind = m.get("kind")
        if kind not in species:
            raise BadInput(f"monsters.{m['id']}: kind không hợp lệ {kind!r}")
        mbounds = {"x": bounds["x"], "d": species[kind]["depths"]}
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), mbounds)
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"monsters.{m['id']}.waypoints phải có đúng 2 điểm")
        for idx, wp in enumerate(wps):
            _pos(f"monsters.{m['id']}.waypoints[{idx}]", wp, mbounds)
        if "target_idx" in m:
            tidx = m["target_idx"]
            if isinstance(tidx, bool) or tidx not in (0, 1):
                raise BadInput(f"monsters.{m['id']}.target_idx phải là 0 hoặc 1")
        st = m.get("state", "patrol")
        if st not in ("patrol", "chase", "recoil"):
            raise BadInput(f"monsters.{m['id']}.state không hợp lệ: {st!r}")
        stl = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{m['id']}.state_ticks_left", stl)
        rdir = m.get("recoil_dir")
        if st == "recoil":
            if stl <= 0:
                raise BadInput(f"monsters.{m['id']}: recoil phải có state_ticks_left > 0")
            if not (isinstance(rdir, list) and len(rdir) == 2 and all(_num(c) and math.isfinite(c) for c in rdir)):
                raise BadInput(f"monsters.{m['id']}: recoil_dir phải là vector đơn vị")
            if abs(math.hypot(rdir[0], rdir[1]) - 1.0) > 1e-3:
                raise BadInput(f"monsters.{m['id']}: recoil_dir phải là vector đơn vị")
        else:
            if stl != 0 or rdir is not None:
                raise BadInput(f"monsters.{m['id']}: trạng thái {st} phải có state_ticks_left == 0 và recoil_dir == null")


def _validate_dish_payload(name, d, menu):
    if not isinstance(d, dict) or set(d) != DISH_PAYLOAD_KEYS:
        raise BadInput(f"{name}: payload món phải có đúng {sorted(DISH_PAYLOAD_KEYS)}")
    if not isinstance(d.get("order_id"), str) or not d["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi khác rỗng")
    if d.get("dish_id") not in menu:
        raise BadInput(f"{name}.dish_id không có trong thực đơn: {d.get('dish_id')!r}")
    bp = d.get("base_price")
    if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
        raise BadInput(f"{name}.base_price phải là số nguyên dương")


def _validate_quan(b, tuning):
    q = tuning["quan"]
    menu = tuning["menu"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        rep = b["reputation"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput("reputation phải nằm trong [reputation_min, reputation_max]")
    if "hand" in b and b["hand"] is not None:
        _validate_dish_payload("quan.hand", b["hand"], menu)
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = q["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    known_stoves = {s["id"] for s in q["stoves"]}
    for s in b.get("stoves", []):
        extra_s = set(s) - QUAN_STOVE_KEYS
        if extra_s:
            raise BadInput(f"stoves.{s['id']}: trường lạ {sorted(extra_s)}")
        if s["id"] not in known_stoves:
            raise BadInput(f"id bếp không tồn tại: {s['id']}")
        if "pos" in s:
            _pos(f"stoves.{s['id']}.pos", s["pos"], qb, axes=("x", "z"))
        if "state" in s and s["state"] not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{s['id']}: state phải là idle, cooking hoặc ready")
        for tk in ("cook_ticks_left", "ready_ticks"):
            if tk in s:
                _nonneg_int(f"stoves.{s['id']}.{tk}", s[tk])
        if "dish" in s and s["dish"] is not None:
            _validate_dish_payload(f"stoves.{s['id']}.dish", s["dish"], menu)
    known_tables = {t["id"] for t in q["tables"]}
    for tb in b.get("tables", []):
        extra_tb = set(tb) - QUAN_TABLE_KEYS
        if extra_tb:
            raise BadInput(f"tables.{tb['id']}: trường lạ {sorted(extra_tb)}")
        if tb["id"] not in known_tables:
            raise BadInput(f"id bàn không tồn tại: {tb['id']}")
        if "pos" in tb:
            _pos(f"tables.{tb['id']}.pos", tb["pos"], qb, axes=("x", "z"))
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    for c in b.get("customers", []):
        extra_c = set(c) - QUAN_CUSTOMER_KEYS
        if extra_c:
            raise BadInput(f"customers.{c['id']}: trường lạ {sorted(extra_c)}")
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known_tables:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
        if c.get("dish_id") not in menu:
            raise BadInput(f"customers.{c['id']}: dish_id không có trong thực đơn")
        for ik in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if ik in c:
                _nonneg_int(f"customers.{c['id']}.{ik}", c[ik])
        if "state" in c and c["state"] not in ("waiting", "eating"):
            raise BadInput(f"customers.{c['id']}: state phải là waiting hoặc eating")
        if "order_status" in c and c["order_status"] not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"customers.{c['id']}: order_status không hợp lệ")
        if "reserved" in c:
            validate_items(c["reserved"])
        for mk in ("base_price", "tip"):
            if mk in c and c[mk] is not None:
                if isinstance(c[mk], bool) or not isinstance(c[mk], int):
                    raise BadInput(f"customers.{c['id']}.{mk} phải là số nguyên")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
