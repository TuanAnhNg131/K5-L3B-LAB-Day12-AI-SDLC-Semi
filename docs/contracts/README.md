# Hợp đồng tích hợp (Contract v1.2 — Phase 3)

Cập nhật từ v1.1 lên v1.2 theo `TICKET-03` ("Mùa Nước Nổi", xem [`0001-itemized-inventory-freshness.md`](../adr/0001-itemized-inventory-freshness.md)).

## 1. Schema file kho (`inventory`, **BREAKING CHANGE v1.2**)

- **Cũ (v1.0–v1.1, bị từ chối bằng mã `2` ở v1.2):** `{"items": {"ca_loc": 1}}`.
- **Mới (v1.2):** `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`.
  - Mảng cá thể duy nhất `id`, `kind` trong 6 nguyên liệu, `fresh ∈ [0, 100]`. Kho rỗng là `{"items":[]}`.
  - File mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json).
  - Cấp ID `I1, I2, ...` tăng liên tục xuyên pha và Ngày, kể cả khi cá thể cũ đã dùng hoặc bỏ.
  - Sắp theo `id` khi xuất file kho (`gather --inventory-out`), giữ đủ độ chính xác cho ngưỡng `30`.

## 2. Độ tươi, ươn, giữ chỗ và giá

- **Hao tươi:** Hàng mới sinh `fresh = 100` (bắt đầu hao từ bước sau). Giỏ `gather` giảm `0.5/s` (`2/240` mỗi tick), kho `quan` giảm `0.25/s` (`1/240` mỗi tick, kể cả hàng đang giữ chỗ). `pause` dừng hao tươi; Shop và món đang nấu/chín/cầm tay không hao.
- **Ươn (`fresh < 30`):** So trước khi làm tròn. Phát `spoiled` (`{"item_id", "kind", "location": "hold"|"stock"}`) đúng một lần khi vượt từ `≥ 30` xuống `< 30` (theo `id`). Hàng ươn vẫn chiếm ô giỏ/kho nhưng không dùng để giữ chỗ hay nấu.
- **Giữ chỗ theo `id`:** Chọn các cá thể chưa ươn tươi nhất cho từng nguyên liệu trong công thức (hòa lấy `id` nhỏ theo `id_key`). Khi giữ chỗ có cá thể vừa ươn, nhả toàn bộ phần giữ của đơn đó và thử giữ lại **một lần** (xử lý các đơn bị ảnh hưởng theo `(order_tick, table_id)`); nếu thiếu chuyển đơn thành `unfulfillable`.
- **Giá theo tươi:** Khi `cook_started`, tiêu đúng các `id` đang giữ và chốt `base_price = floor(giá niêm yết × trung bình fresh / 100)`. Boa tính `floor(base_price × tip_rate)` trên giá đã chốt.

## 3. Thay đổi Scenario & JSONL v1.2

- `gather.hold`, `quan.stock`, `shop.stock`, `cook_started.data.items` (sắp theo `(kind, id)`), `monster_hit.data.lost` và `faint.data.lost` (theo thứ tự bỏ LIFO) đều là mảng cá thể `{id, kind, fresh}`.
- `quan.customers[].reserved` là mảng chuỗi `id` cá thể; mọi `id` vật lý giữa `stock` và giữ chỗ phải duy nhất và khớp công thức.
