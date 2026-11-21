"""Chế độ Một Ngày (`day`) v1.2: ghép gather -> quan -> shop xuyên 1..5 Ngày với kho cá thể."""

import copy

from ..ids import sort_by_id
from ..inventory import item_to_public
from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, max_days=1):
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        self.max_days = int(max_days)
        self.gather_tpl = scenario.get("gather", {})
        self.quan_tpl = scenario.get("quan", {})
        d_cfg = scenario.get("day", {})

        self.money = int(d_cfg.get("money", 0))
        self.earned = int(d_cfg.get("earned", 0))
        self.reputation = float(d_cfg.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = {k: int(v) for k, v in d_cfg.get("upgrades", {}).items() if int(v) > 0}
        self.active_upgrades = dict(self.upgrades)

        self.day_plans = {}
        for pl in tuning["day_plan"]:
            self.day_plans[pl["day"]] = {
                "dishes": dict(pl["dishes"]),
                "ingredients": dict(pl["ingredients"]),
            }
        for ov in d_cfg.get("day_plan", []):
            dnum = int(ov["day"])
            dishes = dict(ov["dishes"])
            ings = {}
            for did, cnt in dishes.items():
                for k, qty in tuning["menu"][did]["recipe"].items():
                    ings[k] = ings.get(k, 0) + qty * cnt
            self.day_plans[dnum] = {
                "dishes": dishes,
                "ingredients": {k: ings[k] for k in sorted(ings)},
            }

        self.day = 1
        self.days_completed = 0
        self.done = False
        self.reason = None

        self.phase = "gather"
        self.sub = None
        self.shop_stock = []
        self.shop_phase_tick = 0
        self.shop_time_left = 0
        self._pending_init = []
        self.last_shift_stats = {}
        self.total_dish_sales = {}
        self.total_served = 0
        self.total_left = 0

        self._start_day(1)

    @property
    def phase_tick(self) -> int:
        if self.sub is not None:
            return self.sub.phase_tick
        return self.shop_phase_tick

    @property
    def time_left_ticks(self) -> int:
        if self.sub is not None:
            return self.sub.time_left_ticks
        return self.shop_time_left

    def _plan_copy(self, day_num=None) -> dict:
        pl = self.day_plans[self.day if day_num is None else day_num]
        return {"dishes": dict(pl["dishes"]), "ingredients": dict(pl["ingredients"])}

    def _effective_tuning(self) -> dict:
        t = copy.deepcopy(self.tuning)
        shop_upgs = t["shop"]["upgrades"]
        oxy_lvl = self.active_upgrades.get("oxygen", 0)
        if oxy_lvl > 0:
            for item in shop_upgs["oxygen"]:
                if item["level"] == oxy_lvl:
                    t["gather"]["oxygen_max_s"] = item["oxygen_max_s"]
                    break
        hp_lvl = self.active_upgrades.get("hp", 0)
        if hp_lvl > 0:
            for item in shop_upgs["hp"]:
                if item["level"] == hp_lvl:
                    t["gather"]["hp_max"] = item["hp_max"]
                    break
        return t

    def _gather_scenario_for_day(self, day_num: int) -> dict:
        if day_num == 1 or "hold" not in self.gather_tpl:
            return self.gather_tpl
        tpl = dict(self.gather_tpl)
        tpl["hold"] = [{"id": self.ids.new("I"), "kind": it["kind"], "fresh": it["fresh"]} for it in self.gather_tpl["hold"]]
        return tpl

    def _start_day(self, day_num: int):
        self.day = day_num
        self.phase = "gather"
        self.shop_stock = []
        eff_t = self._effective_tuning()
        self.sub = GatherSim(
            eff_t, self._gather_scenario_for_day(day_num), self.rng, self.ids,
            day=self.day, money=self.money, earned=self.earned, reputation=self.reputation,
        )
        self._pending_init.extend([
            ("gather", self.day, "day_start", {}),
            ("gather", self.day, "day_plan", self._plan_copy(self.day)),
            ("gather", self.day, "phase_start", {}),
        ])

    def pop_init_events(self):
        ev, self._pending_init = self._pending_init, []
        return ev

    def snapshot(self) -> dict:
        if self.sub is not None:
            snap = self.sub.snapshot()
        else:
            snap = {"stock": [item_to_public(it) for it in sort_by_id(self.shop_stock)]}
        snap["day"] = self.day
        snap["day_plan"] = self._plan_copy(self.day)
        snap["upgrades"] = {k: self.upgrades[k] for k in sorted(self.upgrades)}
        snap["active_upgrades"] = {k: self.active_upgrades[k] for k in sorted(self.active_upgrades)}
        return snap

    def step(self, inp):
        out = []
        phase_changed = False

        if self.phase == "gather":
            ev = self.sub.step(inp)
            for nm, dt in ev:
                out.append(("gather", self.day, nm, dt))
            if self.sub.done:
                inv = self.sub.internal_inventory_items()
                allowed = set(self.day_plans[self.day]["dishes"].keys())
                self.sub = QuanSim(
                    self.tuning, self.quan_tpl, self.rng, self.ids,
                    inventory=inv, allowed_dishes=allowed,
                    initial_money=self.money, initial_earned=self.earned,
                    initial_reputation=self.reputation,
                )
                self.phase = "quan"
                out.append(("quan", self.day, "phase_start", {}))
                phase_changed = True

        elif self.phase == "quan":
            ev = self.sub.step(inp)
            for nm, dt in ev:
                out.append(("quan", self.day, nm, dt))
            self.money = self.sub.money
            self.earned = self.sub.earned
            self.reputation = self.sub.reputation
            if self.sub.done:
                self.last_shift_stats = {
                    "day": self.day,
                    "served": self.sub.served_count,
                    "left": self.sub.left_count,
                    "shift_earned": self.sub.shift_earned,
                    "tips": self.sub.shift_tips,
                    "reputation": self.reputation,
                }
                self.total_served += self.sub.served_count
                self.total_left += self.sub.left_count
                for did, cnt in self.sub.dish_sales.items():
                    self.total_dish_sales[did] = self.total_dish_sales.get(did, 0) + cnt
                self.shop_stock = [dict(it) for it in sort_by_id(self.sub.stock)]
                self.sub = None
                self.phase = "shop"
                self.shop_phase_tick = 0
                self.shop_time_left = int(self.tuning["shop"]["max_ticks"])
                out.append(("shop", self.day, "phase_start", {}))
                phase_changed = True

        elif self.phase == "shop":
            self.shop_phase_tick += 1
            self.shop_time_left = max(0, self.shop_time_left - 1)
            if inp.buy is not None:
                self._handle_buy(inp.buy, out)
            if inp.pressed("shop_done") or self.shop_time_left <= 0:
                end_reason = "done" if inp.pressed("shop_done") else "time"
                out.append(("shop", self.day, "shop_end", {"reason": end_reason}))
                self.days_completed += 1
                if self.days_completed >= self.max_days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.active_upgrades = dict(self.upgrades)
                    self._start_day(self.day + 1)
                    out.extend(self.pop_init_events())
                    phase_changed = True

        return out, phase_changed

    def _handle_buy(self, action: str, out: list):
        upgs_cfg = self.tuning["shop"]["upgrades"]
        if action not in upgs_cfg:
            out.append(("shop", self.day, "buy_failed", {"action": action, "reason": "unknown"}))
            return
        cur_lvl = self.upgrades.get(action, 0)
        tiers = upgs_cfg[action]
        nxt = next((item for item in tiers if item["level"] == cur_lvl + 1), None)
        if nxt is None:
            out.append(("shop", self.day, "buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = int(nxt["price"])
        if self.money < price:
            out.append(("shop", self.day, "buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = int(nxt["level"])
        out.append(("shop", self.day, "bought", {
            "upgrade": action,
            "level": int(nxt["level"]),
            "price": price,
            "money": self.money,
        }))
