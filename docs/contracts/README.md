# Hợp đồng tích hợp (Contract v1.1 — Phase 2)

Cập nhật từ v1.0 lên v1.1 theo `TICKET-02`. Đánh dấu rõ thay đổi để mọi module (`gather`, `quan`, `day`, `client/ui`) đồng bộ.

## 1. Schema file kho (`inventory`, Contract G)

- Giữ nguyên cấu trúc v1.0: `{"items": {kind: số nguyên dương}}`, rỗng là `{"items":{}}`.
- **Mở rộng danh mục lên 6 nguyên liệu (`KINDS_V11`):** `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`.
- File mẫu: [`inventory.sample.json`](inventory.sample.json).
- Trong chế độ `day`, kết thúc `gather` tự bàn giao kho trong bộ nhớ sang `quan` (ngất giao `{}`), còn khi chạy 2 tiến trình rời vẫn dùng `--inventory-out` / `--inventory`.

## 2. Giao diện giữa `sim/*` và `client/ui`

- Hỗ trợ thêm `--mode day --days 1..5`.
- `GET /state`: Bổ sung `paused`, `menu`, `shop_cfg`, và với `mode == "day"` có thêm `day`, `day_plan`, `upgrades`, `active_upgrades`, `max_days`, `days_completed`, `last_shift_stats`, `total_served`, `total_left`, `total_dish_sales`.
- `POST /input`: Nhận thêm `pause` (bool), `shop_done` (bool) và `buy` (chuỗi `"oxygen"` / `"hp"`).

## 3. Danh sách sự kiện bổ sung từ v1.1

| Pha | Sự kiện (`name`) | Trường `data` | Điều kiện phát |
|---|---|---|---|
| Toàn lượt / `day` | `paused` / `resumed` | `{}` | Cạnh lên nút `pause` |
| `day` | `day_start` / `phase_start` | `{}` | Khởi đầu ngày mới / chuyển pha (`gather`/`quan`/`shop`) |
| `day` | `day_plan` | `{"dishes": {...}, "ingredients": {...}}` | Công bố kế hoạch ngày cùng `day_start` |
| `gather` | `fish_spawned` | `{"id", "kind", "pos"}` | Tại `phase_tick = 360·k`, nếu `< 12` đàn và có điểm cách đàn sống `> 1 m` |
| `gather` | `monster_hit` | `{"monster_id", "hp", "lost", "pos"}` | Chạm Cá Sấu (`d >= 10`, hết bất tử); `lost` theo LIFO |
| `gather` | `faint` | `{"cause": "choke"\|"monster", "lost", "hp": 0}` | Máu chạm `0`; `lost` là phần giỏ còn lại theo LIFO |
| `shop` | `bought` | `{"upgrade", "level", "price", "money"}` | Mua nâng cấp hợp lệ (`oxygen`/`hp`) |
| `shop` | `buy_failed` | `{"action", "reason"}` | `funds` / `max_level` / `out_of_stock` / `unknown` |
| `shop` | `shop_end` | `{"reason": "done"\|"time"}` | Đóng bằng `shop_done` hoặc hết `600` tick |
