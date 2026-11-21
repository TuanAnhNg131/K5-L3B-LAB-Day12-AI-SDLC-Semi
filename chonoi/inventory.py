"""File kho v1.2 (kho cá thể): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}.

Độ tươi dùng đơn vị nguyên 1/240 điểm (FRESH_SCALE = 240) hoặc Fraction để so sánh chính xác tại ngưỡng 30
và tính floor giá món mà không bị sai số dấu phẩy động.
Đọc: từ chối file kho đếm cũ / sai schema / id trùng / kind lạ / fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: sắp theo id, qua file tạm cùng thư mục rồi thay thế nguyên tử, giữ đủ độ chính xác float.
"""

from fractions import Fraction
import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_V11 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS_V11
FRESH_SCALE = 240


def to_fresh_units(v):
    """Đổi giá trị độ tươi [0, 100] sang đơn vị 1/240 (int nếu khớp chính xác IEEE-754, ngược lại Fraction)."""
    f = Fraction(str(v)) * FRESH_SCALE
    if f.denominator == 1:
        return int(f)
    cand = int(round(float(f)))
    if float(Fraction(cand, FRESH_SCALE)) == float(v):
        return cand
    return f


def decay_per_tick_units(decay_per_s):
    """Tốc độ hao mỗi tick theo đơn vị 1/240 (0.5/s -> 2, 0.25/s -> 1)."""
    f = Fraction(str(decay_per_s)) * FRESH_SCALE / 60
    return int(f) if f.denominator == 1 else f


def fresh_to_json(u):
    if isinstance(u, int):
        return u // FRESH_SCALE if u % FRESH_SCALE == 0 else u / FRESH_SCALE
    r = u / FRESH_SCALE
    return int(r) if r.denominator == 1 else float(r)


def item_to_public(it: dict) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": fresh_to_json(it["u"])}


def calc_fresh_price(list_price: int, units_list: list) -> int:
    """floor(giá niêm yết × trung bình fresh / 100) chính xác bằng số hữu tỷ."""
    total_u = sum((u if isinstance(u, Fraction) else Fraction(u) for u in units_list), Fraction(0))
    return int((Fraction(list_price) * total_u) // (len(units_list) * 100 * FRESH_SCALE))


def validate_items(items, kinds=KINDS_V11):
    """Kiểm tra map đếm nguyên liệu dương (dùng cho day_plan.ingredients)."""
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_item_list(items, kinds=KINDS_V11) -> list:
    """Kiểm tra mảng cá thể [{id, kind, fresh}] v1.2; từ chối kho đếm kiểu cũ."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể (kho đếm cũ không hợp lệ ở v1.2)")
    seen = set()
    out = []
    for idx, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"items[{idx}]: mỗi cá thể phải có đúng khóa id, kind, fresh")
        iid = it["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{idx}]: id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"items[{idx}]: trùng id {iid}")
        seen.add(iid)
        kind = it["kind"]
        if kind not in kinds:
            raise BadInput(f"items[{idx}]: nguyên liệu lạ {kind!r}")
        fr = it["fresh"]
        if isinstance(fr, bool) or not isinstance(fr, (int, float)) or not math.isfinite(fr) or not (0 <= fr <= 100):
            raise BadInput(f"items[{idx}]: fresh phải thuộc [0, 100]")
        out.append({"id": iid, "kind": kind, "u": to_fresh_units(fr)})
    return out


def read_inventory(path: str, kinds=KINDS_V11) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_item_list(data["items"], kinds)


def write_inventory(path: str, items: list):
    pub = sort_by_id([item_to_public(it) if "u" in it else dict(it) for it in items])
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": pub}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
