"""Đọc game.contract.json và kiểm dải hợp lệ của tuning v1.1 (TICKET-02, Test Contract v1.1)."""

import json
import os

from .errors import BadInput
from .inventory import KINDS_V11

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")

NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    validate_tuning(c.get("tuning"))
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_range(name, r, lo_min, hi_max, allow_eq=False):
    if not isinstance(r, list) or len(r) != 2 or not all(_num(c) for c in r):
        raise BadInput(f"tuning.{name} phải là [lo, hi]")
    ok = r[0] <= r[1] if allow_eq else r[0] < r[1]
    if not (lo_min <= r[0] and r[1] <= hi_max and ok):
        raise BadInput(f"tuning.{name} nằm ngoài miền [{lo_min}, {hi_max}]")


def _validate_gather(g):
    """Dải hợp lệ Test Contract v1.1."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or not set(FISH_KINDS) <= set(fy):
        raise BadInput(f"tuning.gather.fish_yield phải có đủ {FISH_KINDS}")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {NODE_KINDS}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(NODE_KINDS):
        raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút mỗi loại {NODE_KINDS}")

    _int_between("gather.fish_max", g.get("fish_max"), 1, 100)
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, g["fish_max"])
    if not _num(g.get("fish_speed")) or g["fish_speed"] <= 0:
        raise BadInput("tuning.gather.fish_speed phải > 0")
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    if not _num(g.get("fish_spawn_clearance")) or g["fish_spawn_clearance"] < 0:
        raise BadInput("tuning.gather.fish_spawn_clearance phải >= 0")
    _validate_range("gather.fish_x", g.get("fish_x"), b["x"][0], b["x"][1])
    fx_lo, fx_hi = g["fish_x"]
    fspawn_x = g.get("fish_spawn_x")
    if not isinstance(fspawn_x, list) or not fspawn_x or not all(_num(x) and fx_lo <= x <= fx_hi for x in fspawn_x):
        raise BadInput("tuning.gather.fish_spawn_x phải nằm trong fish_x")
    fdepths = g.get("fish_depths")
    fsdepths = g.get("fish_spawn_depths")
    fweights = g.get("fish_weights")
    for fname, obj in (("fish_depths", fdepths), ("fish_spawn_depths", fsdepths), ("fish_weights", fweights)):
        if not isinstance(obj, dict) or set(obj) != set(FISH_KINDS):
            raise BadInput(f"tuning.gather.{fname} phải có đúng khóa {FISH_KINDS}")
    for k in FISH_KINDS:
        _validate_range(f"gather.fish_depths.{k}", fdepths[k], g["surface_depth"] + 1e-6, b["d"][1])
        d_lo, d_hi = fdepths[k]
        s_list = fsdepths[k]
        if not isinstance(s_list, list) or not s_list or not all(_num(d) and d_lo <= d <= d_hi for d in s_list):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải nằm trong fish_depths.{k}")
        if not _num(fweights[k]) or fweights[k] <= 0:
            raise BadInput(f"tuning.gather.fish_weights.{k} phải > 0")

    monsters = g.get("monsters")
    if not isinstance(monsters, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    _int_between("gather.monsters.invuln_ticks", monsters.get("invuln_ticks"), 0, 10_000)
    _between("gather.monsters.loss_ratio", monsters.get("loss_ratio"), 0, 1)
    species = monsters.get("species")
    if not isinstance(species, dict) or "ca_sau" not in species:
        raise BadInput("tuning.gather.monsters.species phải có ca_sau")
    for sk, sp in species.items():
        if not isinstance(sp, dict):
            raise BadInput(f"tuning.gather.monsters.species.{sk} phải là object")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "hit_radius"):
            if not _num(sp.get(key)) or sp[key] <= 0:
                raise BadInput(f"tuning.gather.monsters.species.{sk}.{key} phải > 0")
        if not _num(sp.get("exit_radius")) or sp["exit_radius"] < sp["detect_radius"]:
            raise BadInput(f"tuning.gather.monsters.species.{sk}.exit_radius phải >= detect_radius")
        _validate_range(f"gather.monsters.species.{sk}.depths", sp.get("depths"), b["d"][0], b["d"][1])
        _int_between(f"gather.monsters.species.{sk}.recoil_ticks", sp.get("recoil_ticks"), 1, 10_000)
        if not _num(sp.get("recoil_dist")) or sp["recoil_dist"] < 0:
            raise BadInput(f"tuning.gather.monsters.species.{sk}.recoil_dist phải >= 0")
    spawns = monsters.get("spawns")
    if not isinstance(spawns, list) or not spawns:
        raise BadInput("tuning.gather.monsters.spawns phải là mảng không rỗng")
    mseen = set()
    for spw in spawns:
        if not isinstance(spw, dict) or not isinstance(spw.get("id"), str) or spw["id"] in mseen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con cần id duy nhất")
        mseen.add(spw["id"])
        if spw.get("kind") not in species:
            raise BadInput(f"tuning.gather.monsters.spawns.{spw['id']}: kind không hợp lệ")
        sp_bounds = {"x": b["x"], "d": species[spw["kind"]]["depths"]}
        _pos_in(f"gather.monsters.spawns.{spw['id']}.pos", spw.get("pos"), sp_bounds, ("x", "d"))
        wps = spw.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"tuning.gather.monsters.spawns.{spw['id']}.waypoints phải có đúng 2 điểm")
        for idx, wp in enumerate(wps):
            _pos_in(f"gather.monsters.spawns.{spw['id']}.waypoints[{idx}]", wp, sp_bounds, ("x", "d"))
        _int_between(f"gather.monsters.spawns.{spw['id']}.from_day", spw.get("from_day"), 1, 5)


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ v1.1
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null khi chưa bật mở rộng cháy món")
    for dish_id, d in menu.items():
        price, cook, rec = d.get("price"), d.get("cook_s"), d.get("recipe")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        if not isinstance(rec, dict) or not rec:
            raise BadInput(f"menu.{dish_id}: recipe phải là object khác rỗng")
        for k, qty in rec.items():
            if k not in KINDS_V11 or isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
                raise BadInput(f"menu.{dish_id}.recipe.{k} không hợp lệ")

    plans = t.get("day_plan")
    if not isinstance(plans, list) or len(plans) != 5:
        raise BadInput("tuning.day_plan phải có đúng 5 ngày")
    for expected_day, pl in enumerate(plans, 1):
        if not isinstance(pl, dict) or pl.get("day") != expected_day:
            raise BadInput(f"tuning.day_plan[{expected_day - 1}] phải có day == {expected_day}")
        dishes = pl.get("dishes")
        ings = pl.get("ingredients")
        if not isinstance(dishes, dict) or not dishes or not isinstance(ings, dict):
            raise BadInput(f"tuning.day_plan ngày {expected_day}: thiếu dishes/ingredients")
        calc = {}
        for did, cnt in dishes.items():
            if did not in menu or isinstance(cnt, bool) or not isinstance(cnt, int) or cnt <= 0:
                raise BadInput(f"tuning.day_plan ngày {expected_day}: món {did!r} không hợp lệ")
            for k, qty in menu[did]["recipe"].items():
                calc[k] = calc.get(k, 0) + qty * cnt
        if ings != calc:
            raise BadInput(f"tuning.day_plan ngày {expected_day}: ingredients không khớp tổng công thức")

    shop = t.get("shop")
    if not isinstance(shop, dict):
        raise BadInput("thiếu tuning.shop")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 100_000)
    upgs = shop.get("upgrades")
    if not isinstance(upgs, dict) or not {"oxygen", "hp"} <= set(upgs):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    for uid, field, lo, hi in (("oxygen", "oxygen_max_s", 10, 120), ("hp", "hp_max", 1, 99)):
        arr = upgs.get(uid)
        if not isinstance(arr, list) or not arr:
            raise BadInput(f"tuning.shop.upgrades.{uid} phải là mảng không rỗng")
        for idx, item in enumerate(arr, 1):
            if not isinstance(item, dict) or item.get("level") != idx:
                raise BadInput(f"tuning.shop.upgrades.{uid}[{idx - 1}] phải có level == {idx}")
            _int_between(f"shop.upgrades.{uid}[{idx - 1}].price", item.get("price"), 1, 1_000_000)
            _between(f"shop.upgrades.{uid}[{idx - 1}].{field}", item.get(field), lo, hi)
