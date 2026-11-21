# Kế hoạch Phase 2 (TICKET-02 · Test Contract v1.1)

- **Mục tiêu:** Nâng cấp sang Test Contract v1.1 với số liệu chuẩn (6 nguyên liệu, 6 món, 2 bếp, 4 bàn), đàn cá bơi/phản xạ/sinh mới, Cá Sấu Năm Chèo (`M1`, `M2`), chế độ `day` đầy đủ (`DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> Summary`), `pause`, menu/HUD hoàn chỉnh (`≥ 18px`), và tùy biến sáng tạo phần âm thanh/giao diện.
- **Phân công:** `Nguyễn Tuấn Anh` (`@TuanAnhNg131`) đảm nhiệm toàn bộ 4 lát tuần tự.

## Lát công việc & Acceptance Criteria

| Lát | Phạm vi & file chính | AC mục tiêu | Phụ thuộc |
|---|---|---|---|
| **Manifest & Contracts v1.1** | `game.contract.json`, `chonoi/inventory.py`, `chonoi/contract.py`, `chonoi/inputs.py`, `docs/contracts/README.md` | `AC-P2-01` (Tuning chuẩn 6 nguyên liệu, 6 món, 2 bếp, 4 bàn, `day_plan`, `shop`), `AC-P2-02` (`pause`, `shop_done`, `buy`) | Phase 1 |
| **Lát 1 & 2 (`gather` v1.1)** | `chonoi/sim/gather.py` | `AC-P2-03` (8 đàn đầu, cá bơi/đổi hướng/phản xạ/sinh mới), `AC-P2-04` (Cá Sấu Năm Chèo `M1`/`M2`, patrol/chase/hit/recoil/ngất) | `AC-P2-01` |
| **Lát 3 & 4 (`day`, `quan`, `runner`)** | `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/scenario.py`, `chonoi/runner.py`, `chonoi/headless.py` | `AC-P2-05` (`--mode day` 1..5 ngày, lọc món theo `day_plan`), `AC-P2-06` (Shop mua `oxygen`/`hp`, hiệu lực từ Ngày kế), `AC-P2-07` (`pause`/`resumed` & kiểm tra mã `2`) | `AC-P2-02`, `AC-P2-04` |
| **Live UI, QA & Đóng gói P2** | `chonoi/live.py`, `chonoi/web/index.html`, `tests/test_p2_rules.py`, `docs/proof/phase-2/*`, `docs/verification/phase-2.md` | `AC-P2-08` (Menu, intro, pause, HUD `≥ 18px`, WebAudio SFX), `AC-P2-09` (Smoke tích hợp & regression P1), `AC-P2-10` (Hiệu năng `≤ 20s` & tất định byte), `AC-P2-11` (Tài liệu & tag `phase-2`) | Lát 1–4 |

## Rủi ro & biện pháp
- **Sai thứ tự pha/tác vụ ở bước chuyển pha hoặc khi `pause`:** Đối chiếu mục 4.5 TICKET-02, viết test kiểm tra chính xác tick của `day_start`, `phase_start`, `shop_end`, `paused`/`resumed`.
- **Thay đổi số liệu chuẩn làm sai lệch test Phase 1 cũ:** Cập nhật rõ ràng 2 ca test P1 bị ảnh hưởng bởi bảng số chuẩn (8 đàn cá đầu và 4 bàn quán) và giữ nguyên toàn bộ regression logic lõi.
