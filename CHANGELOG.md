# Changelog
## Unreleased

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
