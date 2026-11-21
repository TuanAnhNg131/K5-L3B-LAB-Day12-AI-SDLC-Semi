# ADR-0001: Chuyển sang Kho Cá Thể (`{id, kind, fresh}`) và Độ Tươi Chính Xác (Test Contract v1.2)

- **Trạng thái:** Chấp nhận
- **Ngày, người quyết:** 2026-11-21 · `Nguyễn Tuấn Anh` (`@TuanAnhNg131`)

## Bối cảnh
Ticket-03 ("Mùa Nước Nổi", Test Contract v1.2) thay thế hoàn toàn kho đếm theo loại (`{"items": {kind: count}}`) bằng **kho cá thể** (`{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}`), bổ sung hao hụt độ tươi theo từng tick (`0.5/s` trong `gather`, `0.25/s` trong `quan`), sự kiện `spoiled` tại ngưỡng `fresh < 30`, cơ chế giữ chỗ theo `id` (tươi nhất trước, nhả và thử giữ lại một lần khi bị ươn) và tính giá món theo độ tươi trung bình (`floor`).

## Các lựa chọn đã cân nhắc
1. **Dùng số thực `float` trực tiếp (`fresh -= 0.5/60`)**: Rủi ro sai số dấu phẩy động tại ngưỡng `30` (ví dụ `100 - 8400 * (0.5/60)` lệch `1e-13`) và khi xuất/đọc file kho.
2. **Đơn vị nguyên `1/240` điểm tươi + `fractions.Fraction` dự phòng (chọn)**:
   - Quy đổi `1` điểm tươi = `240` đơn vị (`FRESH_SCALE = 240`). Khi đó `0.5/s = 2` đơn vị/tick (`gather`), `0.25/s = 1` đơn vị/tick (`quan`).
   - Với mọi giá trị không chia hết `1/240` từ fixture ngoài, giữ bằng `fractions.Fraction`, so sánh ngưỡng `< 30 * 240` và tính `calc_fresh_price` hoàn toàn chính xác tuyệt đối.
   - Khi ghi file kho (`write_inventory`), ghi đầy đủ độ chính xác float để `read_inventory` khôi phục đúng số đơn vị `1/240` bằng kiểm tra round-trip IEEE-754.

## Quyết định & Thứ tự tích hợp giữ `main` chạy được
1. **Lớp dữ liệu & hợp đồng (`game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`):** Thêm `freshness`, nâng `contract_version` lên `"1.2"`, viết `validate_item_list` và từ chối file kho đếm cũ bằng mã `2`.
2. **Kiểm tra scenario (`chonoi/scenario.py`):** Chuyển `gather.hold`, `quan.stock`, `customers[].reserved` sang schema mới.
3. **Mô phỏng (`chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`):** Cấp phát `I1, I2, ...` liên tục qua `IdAllocator`, hao tươi, `spoiled`, giữ chỗ theo `id` và tính `base_price` theo độ tươi.
4. **UI & Test (`chonoi/web/index.html`, `tests/*`):** Hiển thị độ tươi / nhãn `ƯƠN` trên HUD, cập nhật test P1–P2 theo breaking change và bổ sung `tests/test_p3_rules.py`.

## Bảng phân tích tác động (Impact Analysis)

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Manifest & Hợp đồng | `game.contract.json`, `chonoi/contract.py`, `docs/contracts/inventory.sample.json`, `docs/contracts/README.md` | `test_smoke_p1.py` | `@TuanAnhNg131` |
| Kho & Độ tươi | `chonoi/inventory.py`, `chonoi/scenario.py` | `test_smoke_p1.py`, `test_p1_rules.py`, `test_p3_rules.py` | `@TuanAnhNg131` |
| Lặn (`gather`) | `chonoi/sim/gather.py` | `test_smoke_p1.py`, `test_p1_rules.py`, `test_p2_rules.py`, `test_p3_rules.py` | `@TuanAnhNg131` |
| Quán (`quan`) & Ngày (`day`) | `chonoi/sim/quan.py`, `chonoi/sim/day.py` | `test_p1_rules.py`, `test_p2_rules.py`, `test_p3_rules.py` | `@TuanAnhNg131` |
| Client HUD | `chonoi/web/index.html` | `test_live.py` | `@TuanAnhNg131` |
| Starter Unit Test | `tests/test_python_starter_units.py` | `test_session_steps_gather_and_dock` | `@TuanAnhNg131` |
