# Changelog
## Unreleased

## [v1.0.0] — phase-4 · Test Contract v1.3: Phát hành chính thức (2026-11-21)
- **Contract v1.3 & Benchmark (`game.contract.json`, `chonoi/bench.py`):** Khai báo `bench_cmd` (`1280×720` software framebuffer render cho cảnh lặn sáng, làm nóng `3s`, đo `30s`), đạt `821.88 FPS` trung bình, `280.21 FPS` 1% low và `177.24 ms` load time.
- **Soak Headless 10 Ngày (`chonoi/soak.py`, `chonoi/sim/day.py`):** Hỗ trợ kế hoạch Ngày 6–10 lặp lại D1–D5 và chạy bot tất định `10` Ngày liên tục (`days_completed = 10`, `crashes = 0`, tất định 100%).
- **Khả năng tiếp cận & Phụ đề (`chonoi/web/index.html`):** Bổ sung chế độ tương phản cao (phím `H` và nút bật/tắt lưu qua `localStorage`), 3 cảnh báo rõ chữ + icon (*Thủy quái gần*, *Oxy sắp hết / Hết hơi*, *Khách sắp giận*) và thanh phụ đề SFX.
- **Đóng gói & Tài liệu:** Thêm [`LICENSE`](LICENSE) (MIT), cập nhật [`CREDITS.md`](CREDITS.md), [`docs/release-v1.0.0.md`](docs/release-v1.0.0.md), [`docs/retro.md`](docs/retro.md) (rà lại hành động P2), [`docs/members/TuanAnhNg131.md`](docs/members/TuanAnhNg131.md), lưu bằng chứng `docs/proof/phase-4/`, gắn tag `phase-4` và `v1.0.0`.

## [phase-3] — Test Contract v1.2: Mùa Nước Nổi & Độ Tươi (2026-11-21)
- **BREAKING CHANGE — Kho đếm → Kho cá thể (`chonoi/inventory.py`, `chonoi/scenario.py`, `docs/adr/0001-itemized-inventory-freshness.md`):**
  - Chuyển schema kho sang `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}` (`gather.hold`, `quan.stock`, `shop.stock`, `cook_started.items`, `monster_hit.lost`, `faint.lost`).
  - Các file kho đếm kiểu cũ (`{"items":{"ca_loc":1}}`) hoặc scenario dùng dạng chuỗi/map cũ trả mã thoát `2`.
  - Hướng dẫn chuyển đổi fixture: chuyển `hold`/`stock` thành mảng cá thể `{id, kind, fresh}` (hoặc `[]` nếu rỗng) và chuyển `customers[].reserved` thành mảng `id` cá thể.
- **Độ tươi & Giữ chỗ (`chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`):**
  - Tính độ tươi chính xác tuyệt đối bằng đơn vị `1/240` + `Fraction` (`0.5/s` tại `gather`, `0.25/s` tại `quan`, `pause` dừng hao, món chín & Shop không hao).
  - Phát `spoiled` một lần theo `id` khi vượt từ `≥ 30` xuống `< 30`.
  - Giữ chỗ lấy cá thể chưa ươn tươi nhất (hòa lấy `id` nhỏ); khi phần giữ bị ươn, nhả toàn bộ và thử giữ lại một lần theo `(order_tick, table_id)`, thiếu thì chuyển `unfulfillable`.
  - Chốt `base_price = floor(giá niêm yết × trung bình fresh / 100)` khi `cook_started`, boa tính trên giá đã chốt.
  - Cấp `I1, I2, ...` liên tục qua pha và Ngày (`IdAllocator`).
- **HUD & Kiểm thử (`chonoi/web/index.html`, `tests/test_p3_rules.py`):** Hiển thị độ tươi từng ô giỏ, cảnh báo `ƯƠN` (< 30%), cập nhật test P1–P2 theo v1.2 và lưu bằng chứng tại `docs/proof/phase-3/`.

## [phase-2] — Test Contract v1.1: Một ngày ở chợ nổi (2026-11-21)
- **Tuning chuẩn v1.1 (`game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`):** Thêm `ca_keo`, `keo_neo`, nút `N5/N6`, 2 bếp (`B1..B2`), 4 bàn (`T1..T4`), 6 món thực đơn, kế hoạch ngày `D1–D5` (`day_plan`) và cấu hình `shop` nâng cấp `oxygen`/`hp`.
- **Gather v1.1 (`chonoi/sim/gather.py`):** Khởi tạo `8` đàn cá theo trọng số loài, cá bơi `1.5 m/s`, đổi hướng mỗi `120` tick, phản xạ biên/góc, sinh thêm mỗi `360` tick (trần `12`); bổ sung Cá Sấu Năm Chèo (`M1` từ Ngày 1, `M2` từ Ngày 3) tuần tra, rượt đuổi, hit rớt `floor(giỏ/2)` LIFO, `recoil` `60` tick, bất tử `90` tick và ngất `cause="monster"`.
- **Chế độ Một Ngày & Pause (`chonoi/sim/day.py`, `chonoi/runner.py`, `chonoi/headless.py`, `chonoi/scenario.py`):** Hỗ trợ `--mode day --days 1..5`, lọc món theo `day_plan`, Shop cuối ngày mua nâng cấp có hiệu lực từ Ngày kế, hỗ trợ nút `pause`/`shop_done` và lệnh `buy`, kiểm tra mâu thuẫn scenario `day` trả mã `2`.
- **Giao diện & Sáng tạo (`chonoi/live.py`, `chonoi/web/index.html`):** Menu chính, `DayIntro`/`EveningIntro`, Pause overlay (`Esc`/`P`), Shop tương tác, bảng tổng kết `Summary`, HUD chữ lớn `≥ 18px`, cảnh báo viền tím `"Thủy quái!"` / `"Hết hơi!"` và bộ âm thanh WebAudio + cài đặt âm lượng.
- **Test & Proof:** Bổ sung `tests/test_p2_rules.py`, cập nhật 2 ca test P1 theo số chuẩn, lưu bằng chứng tại `docs/proof/phase-2/` và cập nhật `docs/retro.md`.

## [phase-1] — Test Contract v1.0 (2026-11-21)
- **Team & Contract:** Khai báo nhóm `Semi` (`team_size: 1`, `@TuanAnhNg131`) trong `TEAM.md` và `game.contract.json`; chốt hợp đồng tích hợp tại `docs/contracts/README.md`.
- **Gather (`chonoi/sim/gather.py`):** Hoàn thiện sự kiện `dive`/`surface`, tiêu hao & hồi oxy, `oxygen_empty`, đếm ngạt & `choke` mỗi `choke_interval_ticks`, ngất (`faint` mất giỏ LIFO + `gather_end("fainted")`), hái nút ở mặt nước + mọc lại, bắt cá + cooldown + `hold_full`, ưu tiên cập bến.
- **Quán (`chonoi/sim/quan.py` & `chonoi/scenario.py`):** Hoàn thiện lịch khách, giữ chỗ nguyên liệu theo công thức, `no_dish`, chọn tương tác `(khoảng cách, bếp trước bàn, id)`, nấu/nhặt/phục vụ, tính boa & uy tín, khách bỏ đi (`patience`/`closing`), `quan_end`, và kiểm mâu thuẫn scenario trả mã `2`.
- **QA & Harness:** Thêm `tests/test_p1_rules.py`, 2 agent skills (`.agents/skills/verify-contract`, `.agents/skills/phase-release`), lưu bằng chứng tại `docs/proof/phase-1/` và ma trận `docs/verification/phase-1.md`.
