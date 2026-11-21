"""Buổi tối — Mở Quán (`quan`). Luật Phase 1: khách, giữ chỗ, bếp, bưng, phục vụ, tiền, uy tín, đóng ca."""

from decimal import Decimal
import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import validate_items
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allowed_dishes=None,
                 initial_money=0, initial_earned=0, initial_reputation=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.allowed_dishes = set(allowed_dishes) if allowed_dishes is not None else None
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        raw_stock = inventory if inventory is not None else scenario.get("stock", {})
        self.stock = {k: int(v) for k, v in raw_stock.items() if v > 0}
        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.patience_max = int(round(t["patience_s"] * TICK))
        self.eat_max = int(round(t["eat_s"] * TICK))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        default_rep = t["reputation_initial"] if initial_reputation is None else initial_reputation
        self.reputation = float(scenario.get("reputation", default_rep))
        self.stoves = self._init_stoves(t["stoves"], scenario.get("stoves", []))
        self.tables = [dict(tb, pos=[float(c) for c in tb["pos"]])
                       for tb in self._merge(t["tables"], scenario.get("tables", []))]
        self.customers = self._init_customers(scenario.get("customers", []))
        self._validate_cross_links()
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = int(initial_money)
        self.earned = int(initial_earned)
        self.shift_earned = 0
        self.served_count = 0
        self.left_count = 0
        self.shift_tips = 0
        self.dish_sales = {}
        self.done = False
        self.reason = None

    def _validate_dish(self, label, d):
        if not isinstance(d, dict) or set(d) != {"order_id", "dish_id", "base_price"}:
            raise BadInput(f"{label}: payload món không hợp lệ")
        if not isinstance(d.get("order_id"), str) or not d["order_id"]:
            raise BadInput(f"{label}: order_id không hợp lệ")
        if d.get("dish_id") not in self.menu:
            raise BadInput(f"{label}: dish_id không có trong thực đơn")
        if self.allowed_dishes is not None and d.get("dish_id") not in self.allowed_dishes:
            raise BadInput(f"{label}: dish_id {d.get('dish_id')} không thuộc kế hoạch ngày")
        bp = d.get("base_price")
        if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
            raise BadInput(f"{label}: base_price phải là số nguyên dương")

    def _init_stoves(self, defaults, updates):
        stoves = []
        for s in self._merge(defaults, updates):
            state = s.get("state", "idle")
            dish = dict(s["dish"]) if s.get("dish") is not None else None
            cook_left = s.get("cook_ticks_left", 0)
            ready_ticks = s.get("ready_ticks", 0)
            if state == "idle":
                if dish is not None or cook_left != 0 or ready_ticks != 0:
                    raise BadInput(f"bếp {s['id']} idle không được mang món hoặc timer dương")
            elif state == "cooking":
                self._validate_dish(f"bếp {s['id']}", dish)
                if cook_left <= 0 or ready_ticks != 0:
                    raise BadInput(f"bếp {s['id']} cooking phải có cook_ticks_left > 0 và ready_ticks == 0")
            elif state == "ready":
                self._validate_dish(f"bếp {s['id']}", dish)
                if cook_left != 0 or ready_ticks < 0:
                    raise BadInput(f"bếp {s['id']} ready phải có cook_ticks_left == 0 và ready_ticks >= 0")
            else:
                raise BadInput(f"trạng thái bếp không hợp lệ: {state}")
            stoves.append({
                "id": s["id"],
                "pos": [float(c) for c in s["pos"]],
                "state": state,
                "dish": dish,
                "cook_ticks_left": cook_left,
                "ready_ticks": ready_ticks,
            })
        return stoves

    def _init_customers(self, raw_customers):
        out = []
        for c in raw_customers:
            cid = c["id"]
            dish_id = c.get("dish_id")
            if dish_id not in self.menu:
                raise BadInput(f"khách {cid}: dish_id không hợp lệ")
            if self.allowed_dishes is not None and dish_id not in self.allowed_dishes:
                raise BadInput(f"khách {cid}: dish_id {dish_id} không thuộc kế hoạch ngày")
            state = c.get("state", "waiting")
            order_tick = c.get("order_tick", 0)
            if state == "eating":
                order_status = c.get("order_status", "served")
                if order_status != "served":
                    raise BadInput(f"khách {cid} đang eating phải có order_status == 'served'")
                eat_left = c.get("eat_ticks_left", 0)
                if eat_left <= 0:
                    raise BadInput(f"khách {cid} đang eating phải có eat_ticks_left > 0")
                patience_left = c.get("patience_ticks_left", 0)
                if not (0 <= patience_left <= self.patience_max):
                    raise BadInput(f"khách {cid}: patience_ticks_left ngoài [0, {self.patience_max}]")
                res = validate_items(c["reserved"]) if "reserved" in c else {}
                if res:
                    raise BadInput(f"khách {cid} eating không được giữ nguyên liệu")
                base_price = c.get("base_price")
                tip = c.get("tip")
                if (isinstance(base_price, bool) or not isinstance(base_price, int) or base_price <= 0 or
                        isinstance(tip, bool) or not isinstance(tip, int) or tip < 0):
                    raise BadInput(f"khách {cid} eating phải khai base_price > 0 và tip >= 0")
            elif state == "waiting":
                order_status = c.get("order_status", "reserved")
                if order_status not in ("reserved", "assigned", "unfulfillable"):
                    raise BadInput(f"khách {cid} waiting có order_status không hợp lệ: {order_status}")
                eat_left = c.get("eat_ticks_left", 0)
                if eat_left != 0:
                    raise BadInput(f"khách {cid} waiting phải có eat_ticks_left == 0")
                patience_left = c.get("patience_ticks_left", self.patience_max)
                if not (1 <= patience_left <= self.patience_max):
                    raise BadInput(f"khách {cid} waiting: patience_ticks_left phải trong [1, {self.patience_max}]")
                if c.get("base_price") is not None or c.get("tip") is not None:
                    raise BadInput(f"khách {cid} waiting chưa được chốt base_price/tip")
                base_price = None
                tip = None
                if order_status == "reserved":
                    recipe = self.menu[dish_id]["recipe"]
                    if "reserved" in c:
                        res = validate_items(c["reserved"])
                        if res != recipe:
                            raise BadInput(f"khách {cid}: phần giữ không khớp công thức {dish_id}")
                    else:
                        res = dict(recipe)
                else:
                    res = validate_items(c["reserved"]) if "reserved" in c else {}
                    if res:
                        raise BadInput(f"khách {cid} {order_status} phải có phần giữ rỗng")
            else:
                raise BadInput(f"khách {cid}: state không hợp lệ: {state}")
            out.append({
                "id": cid,
                "table_id": c["table_id"],
                "dish_id": dish_id,
                "order_tick": order_tick,
                "state": state,
                "patience_ticks_left": patience_left,
                "eat_ticks_left": eat_left,
                "order_status": order_status,
                "reserved": {k: res[k] for k in sorted(res)},
                "base_price": base_price,
                "tip": tip,
            })
        return out

    def _validate_cross_links(self):
        # 1. Kiểm giữ chỗ so với tồn kho theo thứ tự (order_tick, table_id)
        avail = dict(self.stock)
        reserved_custs = [c for c in self.customers if c["order_status"] == "reserved"]
        for c in sorted(reserved_custs, key=lambda x: (x["order_tick"], id_key(x["table_id"]))):
            for k, qty in c["reserved"].items():
                if avail.get(k, 0) < qty:
                    raise BadInput(f"khách {c['id']}: giữ chỗ '{k}' vượt tồn kho khả dụng")
                avail[k] -= qty
        # 2. Kiểm đơn assigned <-> đúng một món ở bếp hoặc tay
        by_id = {c["id"]: c for c in self.customers}
        dishes = []
        if self.hand is not None:
            self._validate_dish("quan.hand", self.hand)
            dishes.append(("hand", self.hand))
        for s in self.stoves:
            if s["dish"] is not None:
                dishes.append((s["id"], s["dish"]))
        seen_orders = set()
        for loc, d in dishes:
            oid = d["order_id"]
            if oid in seen_orders:
                raise BadInput(f"đơn {oid} xuất hiện trùng lặp ở bếp/tay ({loc})")
            seen_orders.add(oid)
            cust = by_id.get(oid)
            if cust is None:
                raise BadInput(f"món ở {loc} tham chiếu đơn không tồn tại: {oid}")
            if cust["state"] != "waiting" or cust["order_status"] != "assigned":
                raise BadInput(f"món ở {loc} gắn với đơn {oid} không ở trạng thái waiting/assigned")
            if d["dish_id"] != cust["dish_id"]:
                raise BadInput(f"món ở {loc} ({d['dish_id']}) không khớp đơn {oid} ({cust['dish_id']})")
        for c in self.customers:
            if c["order_status"] == "assigned" and c["id"] not in seen_orders:
                raise BadInput(f"đơn assigned {c['id']} thiếu món ở bếp hoặc tay")

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel)},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": dict(self.hand) if self.hand is not None else None,
            "stoves": [{
                "id": s["id"],
                "pos": list(s["pos"]),
                "state": s["state"],
                "dish": dict(s["dish"]) if s["dish"] is not None else None,
                "cook_ticks_left": s["cook_ticks_left"],
                "ready_ticks": s["ready_ticks"],
            } for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": list(tb["pos"]), "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": [dict(c, reserved={k: c["reserved"][k] for k in sorted(c["reserved"])})
                          for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        events = []
        # 1. Đồng hồ và các bộ đếm
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in sort_by_id(self.stoves):
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

        # 2. Món nấu xong chuyển ready (ready_ticks = 0) theo id bếp
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", {
                    "stove_id": s["id"],
                    "order_id": s["dish"]["order_id"],
                    "dish_id": s["dish"]["dish_id"],
                }))

        # 3. Di chuyển và tối đa một tương tác
        self._move(inp)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 4. Thanh toán, khách hết kiên nhẫn và đóng ca theo id bàn
        closing = self.time_left_ticks <= 0
        self._process_customers_and_closing(closing, events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))
            return events

        # 5. Khách mới theo lịch (chỉ khi còn giờ)
        if self.random_customers:
            self._maybe_spawn_customer(events)

        return events

    def _handle_interact(self, events):
        rad = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= rad:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= rad:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda x: (x[0], x[1], x[2]))
        if kind == "stove":
            if obj["state"] == "idle":
                waiting_res = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
                if not waiting_res:
                    return
                cust = min(waiting_res, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
                items_list = []
                for k in sorted(cust["reserved"]):
                    qty = cust["reserved"][k]
                    items_list.extend([k] * qty)
                    rem = self.stock.get(k, 0) - qty
                    if rem > 0:
                        self.stock[k] = rem
                    else:
                        self.stock.pop(k, None)
                cust["reserved"] = {}
                cust["order_status"] = "assigned"
                base_price = int(self.menu[cust["dish_id"]]["price"])
                obj["state"] = "cooking"
                obj["dish"] = {"order_id": cust["id"], "dish_id": cust["dish_id"], "base_price": base_price}
                obj["cook_ticks_left"] = int(round(self.menu[cust["dish_id"]]["cook_s"] * TICK))
                obj["ready_ticks"] = 0
                events.append(("cook_started", {
                    "stove_id": obj["id"],
                    "order_id": cust["id"],
                    "dish_id": cust["dish_id"],
                    "items": items_list,
                    "base_price": base_price,
                }))
            elif obj["state"] == "ready" and self.hand is None:
                d = obj["dish"]
                self.hand = d
                obj["state"] = "idle"
                obj["dish"] = None
                obj["cook_ticks_left"] = 0
                obj["ready_ticks"] = 0
                events.append(("dish_picked", {
                    "stove_id": obj["id"],
                    "order_id": d["order_id"],
                    "dish_id": d["dish_id"],
                }))
        else:
            cust = next((c for c in self.customers if c["table_id"] == obj["id"]), None)
            if cust and cust["state"] == "waiting" and self.hand is not None and self.hand["order_id"] == cust["id"]:
                d = self.hand
                self.hand = None
                base_price = d["base_price"]
                min_pat = Decimal(self.patience_max) * Decimal(str(self.t["tip_min_patience_ratio"]))
                eligible = Decimal(cust["patience_ticks_left"]) >= min_pat
                tip = int(math.floor(Decimal(base_price) * Decimal(str(self.t["tip_rate"])))) if eligible else 0
                cust["state"] = "eating"
                cust["order_status"] = "served"
                cust["eat_ticks_left"] = self.eat_max
                cust["base_price"] = base_price
                cust["tip"] = tip
                events.append(("served", {
                    "order_id": cust["id"],
                    "table_id": obj["id"],
                    "dish_id": cust["dish_id"],
                    "patience_ticks_left": cust["patience_ticks_left"],
                    "base_price": base_price,
                    "tip": tip,
                }))

    def _adjust_reputation(self, delta):
        rep = float(round(Decimal(str(self.reputation)) + Decimal(str(delta)), 6))
        lo, hi = float(self.t["reputation_min"]), float(self.t["reputation_max"])
        self.reputation = min(hi, max(lo, rep))

    def _discard_order_dish(self, order_id):
        if self.hand is not None and self.hand["order_id"] == order_id:
            self.hand = None
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == order_id:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

    def _process_customers_and_closing(self, closing, events):
        kept = []
        for c in sorted(self.customers, key=lambda x: id_key(x["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] == 0 or closing:
                    reason = "finished_eating" if c["eat_ticks_left"] == 0 else "closing"
                    amount = c["base_price"] + c["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    self.served_count += 1
                    self.shift_tips += c["tip"]
                    self.dish_sales[c["dish_id"]] = self.dish_sales.get(c["dish_id"], 0) + 1
                    if c["tip"] > 0:
                        self._adjust_reputation(self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "base_price": c["base_price"],
                        "tip": c["tip"],
                        "amount": amount,
                        "reason": reason,
                    }))
                else:
                    kept.append(c)
            else:
                if not closing and c["patience_ticks_left"] == 0:
                    c["reserved"] = {}
                    self._discard_order_dish(c["id"])
                    self._adjust_reputation(self.t["left_reputation_delta"])
                    self.left_count += 1
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "patience",
                        "reputation": self.reputation,
                    }))
                elif closing:
                    c["reserved"] = {}
                    self._discard_order_dish(c["id"])
                    self.left_count += 1
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation,
                    }))
                else:
                    kept.append(c)
        self.customers = kept

    def _maybe_spawn_customer(self, events):
        first = int(self.t["first_customer_tick"])
        interval = int(round(self.t["customer_interval_s"] * TICK))
        if self.phase_tick < first or (self.phase_tick - first) % interval != 0:
            return
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return
        tb = free_tables[0]
        avail = dict(self.stock)
        for c in self.customers:
            for k, qty in c["reserved"].items():
                avail[k] = avail.get(k, 0) - qty
        cookable = [
            dish_id for dish_id in sorted(self.menu)
            if (self.allowed_dishes is None or dish_id in self.allowed_dishes)
            and all(avail.get(k, 0) >= qty for k, qty in self.menu[dish_id]["recipe"].items())
        ]
        if not cookable:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_dish").choice(cookable)
        cid = self.ids.new("C")
        recipe = self.menu[dish_id]["recipe"]
        self.customers.append({
            "id": cid,
            "table_id": tb["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": self.patience_max,
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": {k: recipe[k] for k in sorted(recipe)},
            "base_price": None,
            "tip": None,
        })
        events.append(("customer_arrived", {
            "order_id": cid,
            "table_id": tb["id"],
            "dish_id": dish_id,
        }))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
