# Changelog
## Unreleased

## [phase-1] — Test Contract v1.0 (2026-11-21)
- **Team & Contract:** Khai báo nhóm `Semi` (`team_size: 1`, `@TuanAnhNg131`) trong `TEAM.md` và `game.contract.json`; chốt hợp đồng tích hợp tại `docs/contracts/README.md`.
- **Gather (`chonoi/sim/gather.py`):** Hoàn thiện sự kiện `dive`/`surface`, tiêu hao & hồi oxy, `oxygen_empty`, đếm ngạt & `choke` mỗi `choke_interval_ticks`, ngất (`faint` mất giỏ LIFO + `gather_end("fainted")`), hái nút ở mặt nước + mọc lại, bắt cá + cooldown + `hold_full`, ưu tiên cập bến.
- **Quán (`chonoi/sim/quan.py` & `chonoi/scenario.py`):** Hoàn thiện lịch khách, giữ chỗ nguyên liệu theo công thức, `no_dish`, chọn tương tác `(khoảng cách, bếp trước bàn, id)`, nấu/nhặt/phục vụ, tính boa & uy tín, khách bỏ đi (`patience`/`closing`), `quan_end`, và kiểm mâu thuẫn scenario trả mã `2`.
- **QA & Harness:** Thêm `tests/test_p1_rules.py`, 2 agent skills (`.agents/skills/verify-contract`, `.agents/skills/phase-release`), lưu bằng chứng tại `docs/proof/phase-1/` và ma trận `docs/verification/phase-1.md`.
