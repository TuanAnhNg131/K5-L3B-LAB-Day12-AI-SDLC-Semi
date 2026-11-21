"""Buổi sáng — Lặn & Hái (`gather`). Luật v1.2: bơi, oxy, ngạt, hái, bắt cá, cá bơi/sinh, Cá Sấu, độ tươi."""

import math

from ..ids import id_key, sort_by_id
from ..inventory import decay_per_tick_units, item_to_public, to_fresh_units
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, money=0, earned=0, reputation=None):
        t = tuning["gather"]
        fr = tuning["freshness"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = day
        self.initial_u = to_fresh_units(fr["initial"])
        self.gather_decay_u = decay_per_tick_units(fr["gather_decay_per_s"])
        self.spoiled_u = to_fresh_units(fr["spoiled_below"])

        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)

        self.hold = []  # thứ tự nhặt, cuối mảng là mới nhất
        for it in scenario.get("hold", []):
            item = dict(it) if "u" in it else {"id": it["id"], "kind": it["kind"], "u": to_fresh_units(it["fresh"])}
            self.hold.append(item)
            ids.reserve(item["id"])

        self.phase_tick = 0
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.random_fish = scenario.get("random_fish", True)

        # Nút hái
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for n in self.nodes:
            ids.reserve(n["id"])

        # Đàn cá
        self.fish = []
        if "fish" in scenario:
            for f in scenario["fish"]:
                self.fish.append({
                    "id": f["id"],
                    "kind": f["kind"],
                    "pos": [float(c) for c in f["pos"]],
                    "heading_deg": float(f.get("heading_deg", 0.0)),
                    "age_ticks": int(f.get("age_ticks", 0)),
                })
                ids.reserve(f["id"])
        elif self.random_fish:
            used_pts = set()
            for _ in range(int(t["fish_initial"])):
                f = self._spawn_fish_school(used_points=used_pts)
                if f is None:
                    break
                used_pts.add((f["pos"][0], f["pos"][1]))
                self.fish.append(f)

        # Thủy quái (Cá Sấu Năm Chèo)
        self.monsters = []
        if "monsters" in scenario:
            for m in scenario["monsters"]:
                self.monsters.append({
                    "id": m["id"],
                    "kind": m["kind"],
                    "pos": [float(c) for c in m["pos"]],
                    "waypoints": [[float(c) for c in wp] for wp in m["waypoints"]],
                    "target_idx": int(m.get("target_idx", 1)),
                    "state": m.get("state", "patrol"),
                    "state_ticks_left": int(m.get("state_ticks_left", 0)),
                    "recoil_dir": [float(c) for c in m["recoil_dir"]] if m.get("recoil_dir") is not None else None,
                })
                ids.reserve(m["id"])
        else:
            for sp in t["monsters"]["spawns"]:
                if self.day >= int(sp["from_day"]):
                    self.monsters.append({
                        "id": sp["id"],
                        "kind": sp["kind"],
                        "pos": [float(c) for c in sp["pos"]],
                        "waypoints": [[float(c) for c in wp] for wp in sp["waypoints"]],
                        "target_idx": 1,
                        "state": "patrol",
                        "state_ticks_left": 0,
                        "recoil_dir": None,
                    })
                    ids.reserve(sp["id"])

        self.money = int(money)
        self.earned = int(earned)
        self.reputation = float(tuning["quan"]["reputation_initial"] if reputation is None else reputation)
        self.done = False
        self.reason = None

    def _spawn_fish_school(self, used_points=None, clearance=None):
        weights_map = self.t["fish_weights"]
        spawn_x = self.t["fish_spawn_x"]
        spawn_depths = self.t["fish_spawn_depths"]
        valid_by_kind = {}
        for kind in sorted(weights_map):
            pts = []
            for x in spawn_x:
                for d in spawn_depths[kind]:
                    pt = (float(x), float(d))
                    if used_points is not None and pt in used_points:
                        continue
                    if clearance is not None and any(math.dist(pt, f["pos"]) <= clearance for f in self.fish):
                        continue
                    pts.append(pt)
            if pts:
                valid_by_kind[kind] = pts
        if not valid_by_kind:
            return None
        rng = self.rng.get("fish_spawn")
        kinds = list(valid_by_kind.keys())
        weights = [weights_map[k] for k in kinds]
        kind = rng.choices(kinds, weights=weights, k=1)[0]
        px, pd = rng.choice(valid_by_kind[kind])
        heading = rng.uniform(0.0, 360.0)
        return {
            "id": self.ids.new("F"),
            "kind": kind,
            "pos": [px, pd],
            "heading_deg": heading,
            "age_ticks": 0,
        }

    # --- giao diện cho runner / day -------------------------------------------
    def inventory_items(self) -> list:
        return [item_to_public(it) for it in sort_by_id(self.hold)]

    def internal_inventory_items(self) -> list:
        return [dict(it) for it in sort_by_id(self.hold)]

    def snapshot(self) -> dict:
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel), "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [item_to_public(it) for it in self.hold],
            "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": list(n["pos"]), "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": list(f["pos"]), "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{
                "id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                "waypoints": [list(wp) for wp in m["waypoints"]],
                "target_idx": m["target_idx"], "state": m["state"],
                "state_ticks_left": m["state_ticks_left"],
                "recoil_dir": list(m["recoil_dir"]) if m["recoil_dir"] is not None else None,
            } for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, cooldown, bất tử, hồi nút và hao độ tươi hàng sẵn có đầu bước
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        for it in sort_by_id(self.hold):
            prev_u = it["u"]
            if prev_u > 0:
                it["u"] = max(0, prev_u - self.gather_decay_u)
                if prev_u >= self.spoiled_u and it["u"] < self.spoiled_u:
                    events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))

        # 2. bơi + chặn mép + dive/surface + oxy + ngạt + ngất
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            prev_oxy = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if prev_oxy > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        lost = [item_to_public(it) for it in reversed(self.hold)]
                        self.hold.clear()
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 3. cập nhật thủy quái theo id và xét tối đa một hit
        if self._step_monsters(events):
            return events

        # 4. interact: bến trước, rồi hái (chỉ ở mặt nước)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                rad = self.t["interact_radius"]
                cands = [n for n in self.nodes if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= rad]
                if cands:
                    best = min(cands, key=lambda n: (math.dist(self.pos, n["pos"]), id_key(n["id"])))
                    amount = int(self.t["node_yield"])
                    free = int(self.t["hold_capacity"]) - len(self.hold)
                    if free >= amount:
                        for _ in range(amount):
                            self.hold.append({"id": self.ids.new("I"), "kind": best["kind"], "u": self.initial_u})
                        best["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": best["id"], "kind": best["kind"], "amount": amount}))
                    else:
                        events.append(("hold_full", {"action": "gather", "node_id": best["id"],
                                                     "required": amount, "free": free}))

        # 5. bắt cá (vị trí cá trước khi bơi, chỉ khi hết hồi chiêu và dưới nước)
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_surface:
            rad = self.t["catch_radius"]
            cands = [f for f in self.fish if math.dist(self.pos, f["pos"]) <= rad]
            if cands:
                best = min(cands, key=lambda f: (math.dist(self.pos, f["pos"]), id_key(f["id"])))
                yld = int(self.t["fish_yield"][best["kind"]])
                free = int(self.t["hold_capacity"]) - len(self.hold)
                if free >= yld:
                    for _ in range(yld):
                        self.hold.append({"id": self.ids.new("I"), "kind": best["kind"], "u": self.initial_u})
                    self.fish.remove(best)
                    self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                    events.append(("fish_caught", {"fish_id": best["id"], "kind": best["kind"], "yield": yld}))
                else:
                    events.append(("hold_full", {"action": "catch", "fish_id": best["id"],
                                                 "required": yld, "free": free}))

        # 6. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 7. đàn cá bơi và sinh thêm theo lịch (chỉ khi còn giờ và random_fish bật)
        if self.random_fish:
            self._step_fish(events)

        return events

    def _clamp_monster_pos(self, pos, depths):
        bx = self.t["bounds"]["x"]
        return [
            min(float(bx[1]), max(float(bx[0]), pos[0])),
            min(float(depths[1]), max(float(depths[0]), pos[1])),
        ]

    def _step_monsters(self, events) -> bool:
        mcfg = self.t["monsters"]
        species = mcfg["species"]
        can_hit = []
        for m in sort_by_id(self.monsters):
            sp = species[m["kind"]]
            depths = sp["depths"]
            if m["state"] == "recoil":
                step_d = sp["recoil_dist"] / sp["recoil_ticks"]
                rx, rd = m["recoil_dir"]
                m["pos"] = self._clamp_monster_pos([m["pos"][0] + rx * step_d, m["pos"][1] + rd * step_d], depths)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["state_ticks_left"] = 0
                    m["recoil_dir"] = None
                continue

            in_zone = self.pos[1] >= depths[0]
            dist_p = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol" and in_zone and dist_p <= sp["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (not in_zone or dist_p > sp["exit_radius"]):
                m["state"] = "patrol"

            if m["state"] == "chase":
                step_d = sp["chase_speed"] / TICK
                if dist_p <= step_d:
                    m["pos"] = self._clamp_monster_pos(list(self.pos), depths)
                else:
                    ux = (self.pos[0] - m["pos"][0]) / dist_p
                    ud = (self.pos[1] - m["pos"][1]) / dist_p
                    m["pos"] = self._clamp_monster_pos([m["pos"][0] + ux * step_d, m["pos"][1] + ud * step_d], depths)
            else:
                wp = m["waypoints"][m["target_idx"]]
                step_d = sp["patrol_speed"] / TICK
                dist_w = math.dist(m["pos"], wp)
                if dist_w <= step_d:
                    m["pos"] = self._clamp_monster_pos(list(wp), depths)
                    m["target_idx"] = 1 - m["target_idx"]
                else:
                    ux = (wp[0] - m["pos"][0]) / dist_w
                    ud = (wp[1] - m["pos"][1]) / dist_w
                    m["pos"] = self._clamp_monster_pos([m["pos"][0] + ux * step_d, m["pos"][1] + ud * step_d], depths)
            can_hit.append(m)

        if self.invuln_ticks == 0 and can_hit:
            eligible = []
            for m in can_hit:
                sp = species[m["kind"]]
                if self.pos[1] >= sp["depths"][0] and math.dist(m["pos"], self.pos) <= sp["hit_radius"]:
                    eligible.append(m)
            if eligible:
                hitter = min(eligible, key=lambda m: (math.dist(m["pos"], self.pos), id_key(m["id"])))
                sp = species[hitter["kind"]]
                self.hp = max(0, self.hp - 1)
                drop_n = int(math.floor(len(self.hold) * mcfg["loss_ratio"]))
                lost = [item_to_public(self.hold.pop()) for _ in range(drop_n)]
                self.invuln_ticks = int(mcfg["invuln_ticks"])
                dx = hitter["pos"][0] - self.pos[0]
                dd = hitter["pos"][1] - self.pos[1]
                nrm = math.hypot(dx, dd)
                hitter["recoil_dir"] = [1.0, 0.0] if nrm == 0 else [dx / nrm, dd / nrm]
                hitter["state"] = "recoil"
                hitter["state_ticks_left"] = int(sp["recoil_ticks"])
                events.append(("monster_hit", {
                    "monster_id": hitter["id"],
                    "hp": self.hp,
                    "lost": lost,
                    "pos": list(self.pos),
                }))
                if self.hp <= 0:
                    rem_lost = [item_to_public(it) for it in reversed(self.hold)]
                    self.hold.clear()
                    events.append(("faint", {"cause": "monster", "lost": rem_lost, "hp": 0}))
                    self._finish("fainted", events)
                    return True
        return False

    def _step_fish(self, events):
        turn_ticks = int(self.t["fish_turn_ticks"])
        step_d = self.t["fish_speed"] / TICK
        x_lo, x_hi = self.t["fish_x"]
        turn_rng = self.rng.get("fish_turn")
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = turn_rng.uniform(0.0, 360.0)
            rad = math.radians(f["heading_deg"])
            ux, ud = math.cos(rad), math.sin(rad)
            ox, od = f["pos"]
            nx, nd = ox + ux * step_d, od + ud * step_d
            d_lo, d_hi = self.t["fish_depths"][f["kind"]]
            if ox >= x_lo and nx < x_lo:
                nx = x_lo + (x_lo - nx)
                ux = -ux
            elif ox <= x_hi and nx > x_hi:
                nx = x_hi - (nx - x_hi)
                ux = -ux
            if od >= d_lo and nd < d_lo:
                nd = d_lo + (d_lo - nd)
                ud = -ud
            elif od <= d_hi and nd > d_hi:
                nd = d_hi - (nd - d_hi)
                ud = -ud
            nx = min(float(x_hi), max(float(x_lo), nx))
            nd = min(float(d_hi), max(float(d_lo), nd))
            f["pos"] = [nx, nd]
            f["heading_deg"] = math.degrees(math.atan2(ud, ux)) % 360.0

        spawn_ticks = int(self.t["fish_spawn_ticks"])
        if self.phase_tick > 0 and self.phase_tick % spawn_ticks == 0 and len(self.fish) < int(self.t["fish_max"]):
            nf = self._spawn_fish_school(clearance=float(self.t["fish_spawn_clearance"]))
            if nf is not None:
                self.fish.append(nf)
                events.append(("fish_spawned", {"id": nf["id"], "kind": nf["kind"], "pos": list(nf["pos"])}))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
