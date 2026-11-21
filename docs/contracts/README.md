# Hợp đồng tích hợp (Contract v1.0 — Phase 1)

Chốt tại kickoff Phase 1. Mọi thay đổi schema ở các phase sau phải cập nhật tài liệu này, `CHANGELOG.md` và ghi rõ lý do.

## 1. Schema file kho (`inventory`, Contract G)

- Khớp mục G của PRD-0: chỉ có duy nhất khóa gốc `items`, giá trị là object `kind -> số nguyên dương`.
- Nguyên liệu hợp lệ v1.0 (`KINDS_P1`): `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Bỏ khóa có số lượng `0` khi ghi; kho rỗng là `{"items":{}}`.
- File mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json) (`{"items":{"bong_sung":2,"ca_loc":1}}`).
- Cơ chế bàn giao: `gather --inventory-out <file>` ghi nguyên tử (file tạm cùng thư mục + `os.replace`) đúng một lần khi có `gather_end` (`docked`/`time`/`fainted`; ngất ghi `{"items":{}}`). Dừng do `--ticks` trước khi kết thúc thì không tạo/ghi đè file.

## 2. Giao diện giữa `sim/*` và `client/ui`

`chonoi.live` chạy chung lớp `runner.Session` (60 tick/s) với `chonoi.headless`. UI (`chonoi/web/index.html`) hoàn toàn tách khỏi RNG/luật mô phỏng:
- `GET /state`: Trả về snapshot JSON hiện tại (`tick, sim_tick, mode, phase, phase_tick, state, time_left_ticks, money, earned, reputation, score` + trường riêng từng mode) cùng `meta` (`tuning[mode]`), `events` (40 sự kiện gần nhất), `finished`, `reason`, `error`.
- `POST /input`: Gửi trạng thái phím `{"move": [dx, dy], "interact": bool, "catch": bool}` (`dx, dy ∈ [-1, 1]`). Lớp `LiveInputs` bắt cạnh lên (`false -> true`) giữa hai tick.
- `POST /restart`: Khởi tạo lại lượt chơi cùng seed và scenario.

## 3. Danh sách sự kiện (Test Contract v1.0)

| Pha | Sự kiện (`name`) | Trường `data` | Bên phát & điều kiện |
|---|---|---|---|
| `gather` | `node_regrown` | `{"node_id"}` | `GatherSim`: `regrow_ticks` giảm từ `1` về `0` |
| `gather` | `dive` | `{"pos": [x, d]}` | `GatherSim`: đổi từ mặt nước (`d <= surface_depth`) sang dưới nước |
| `gather` | `surface` | `{"pos": [x, d]}` | `GatherSim`: đổi từ dưới nước sang mặt nước |
| `gather` | `oxygen_empty` | `{"oxygen_ticks": 0}` | `GatherSim`: oxy từ dương chạm `0` ở dưới nước |
| `gather` | `choke` | `{"hp"}` | `GatherSim`: đủ `choke_interval_ticks` dưới nước với oxy `0`, trừ 1 Máu |
| `gather` | `faint` | `{"cause": "choke", "lost": [...], "hp": 0}` | `GatherSim`: Máu về `0`, mất toàn bộ giỏ theo thứ tự LIFO |
| `gather` | `gather` | `{"node_id", "kind", "amount"}` | `GatherSim`: cạnh `interact` ngoài bến, ở mặt nước, đủ chỗ giỏ |
| `gather` | `hold_full` | `{"action": "gather"\|"catch", "node_id"\|"fish_id", "required", "free"}` | `GatherSim`: giỏ không đủ chỗ trống |
| `gather` | `fish_caught` | `{"fish_id", "kind", "yield"}` | `GatherSim`: cạnh `catch` hết hồi chiêu, dưới nước, đủ chỗ giỏ |
| `gather` | `gather_end` | `{"reason": "time"\|"docked"\|"fainted", "inventory": {"items": {...}}}` | `GatherSim`: kết thúc buổi sáng |
| `quan` | `dish_ready` | `{"stove_id", "order_id", "dish_id"}` | `QuanSim`: bếp `cooking` có `cook_ticks_left` về `0` |
| `quan` | `cook_started` | `{"stove_id", "order_id", "dish_id", "items": [...], "base_price"}` | `QuanSim`: `interact` bếp `idle`, lấy đơn `reserved` cũ nhất |
| `quan` | `dish_picked` | `{"stove_id", "order_id", "dish_id"}` | `QuanSim`: `interact` bếp `ready` khi tay trống |
| `quan` | `served` | `{"order_id", "table_id", "dish_id", "patience_ticks_left", "base_price", "tip"}` | `QuanSim`: `interact` bàn có khách `waiting` khớp `order_id` |
| `quan` | `paid` | `{"order_id", "table_id", "base_price", "tip", "amount", "reason": "finished_eating"\|"closing"}` | `QuanSim`: khách `eating` ăn xong hoặc đóng ca |
| `quan` | `customer_left` | `{"order_id", "table_id", "reason": "patience"\|"closing", "reputation"}` | `QuanSim`: khách `waiting` hết kiên nhẫn hoặc đóng ca |
| `quan` | `customer_arrived` | `{"order_id", "table_id", "dish_id"}` | `QuanSim`: tới lịch, có bàn trống và có ít nhất 1 món đủ tồn khả dụng |
| `quan` | `no_dish` | `{}` | `QuanSim`: tới lịch, có bàn trống nhưng không đủ nguyên liệu cho món nào |
| `quan` | `quan_end` | `{"reason": "time", "money", "earned", "shift_earned", "reputation"}` | `QuanSim`: hết giờ ca tối |
