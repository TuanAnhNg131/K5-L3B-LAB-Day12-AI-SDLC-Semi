# Kế hoạch Phase 3 (TICKET-03 · Change Request "Mùa Nước Nổi" · Test Contract v1.2)

- **Mục tiêu:** Triển khai đầy đủ Change Request độ tươi và kho cá thể (`contract_version: "1.2"`), bảo đảm tính toán chính xác tuyệt đối ở ngưỡng `30`, giữ chỗ theo `id`, chốt giá theo độ tươi, từ chối kho đếm cũ với mã `2`, cập nhật HUD và ghi nhận breaking change.
- **Phân công:** `Nguyễn Tuấn Anh` (`@TuanAnhNg131`) thực hiện theo trình tự ADR-0001 để giữ `main` luôn ổn định.

## Lát công việc & Acceptance Criteria

| Lát | Phạm vi & file chính | AC mục tiêu | Phụ thuộc |
|---|---|---|---|
| **ADR & Schema Migration** | `docs/adr/0001-itemized-inventory-freshness.md`, `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `docs/contracts/*` | `AC-P3-01` (Contract v1.2 + `freshness`, từ chối kho đếm cũ mã `2`) | Phase 2 |
| **Gather Độ tươi & LIFO** | `chonoi/scenario.py`, `chonoi/sim/gather.py` | `AC-P3-02` (Cấp `I1, I2...`, hao `0.5/s`, `spoiled` tại `<30`, `lost` LIFO cá thể) | `AC-P3-01` |
| **Quán & Ngày Độ tươi** | `chonoi/sim/quan.py`, `chonoi/sim/day.py` | `AC-P3-03` (Hao `0.25/s`, giữ theo `id` tươi nhất, nhả & thử giữ lại 1 lần khi ươn, `unfulfillable`), `AC-P3-04` (Giá `floor` theo độ tươi & boa), `AC-P3-05` (`day` ID liên tục, không hao khi đổi pha/Shop) | `AC-P3-02` |
| **UI, Migration Test & Release P3** | `chonoi/web/index.html`, `tests/*`, `CHANGELOG.md`, `docs/verification/phase-3.md`, `docs/proof/phase-3/*` | `AC-P3-06` (HUD đọc độ tươi & nhãn `ƯƠN`), `AC-P3-07` (Smoke 2 tiến trình & ngưỡng 30), `AC-P3-08` (Regression P1–P2, `CHANGELOG` breaking change, tag `phase-3`) | Lát 1–3 |

## Rủi ro & biện pháp
- **Sai lệch làm tròn float tại ngưỡng `30` hoặc khi đọc lại file kho:** Dùng đơn vị nguyên `240/điểm` kết hợp `Fraction` và kiểm tra round-trip khi đọc file kho.
- **Bàn giao trong `day` hoặc scenario `quan` giữ lại ID trùng:** `GatherSim.internal_inventory_items()` truyền trực tiếp bản sao đơn vị chính xác, và `DaySim` giữ `IdAllocator` duy nhất xuyên suốt mọi ngày để ID `I1, I2...` không bao giờ cấp lại.
