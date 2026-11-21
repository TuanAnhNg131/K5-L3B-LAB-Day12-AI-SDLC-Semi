# Kế hoạch Phase 4 (TICKET-04 · Test Contract v1.3 & Phát hành v1.0.0)

- **Mục tiêu:** Hoàn thiện Test Contract v1.3 (`bench_cmd`, `soak_cmd`), nâng cấp khả năng tiếp cận (3 cảnh báo rõ chữ + biểu tượng, chế độ tương phản cao, phụ đề SFX), kiểm thử từ clone sạch (≤ 3 lệnh), tổng kết retro cuối, viết phản tư cá nhân, đóng gói bản phát hành và gắn đồng thời tag `phase-4` và `v1.0.0`.
- **Phân công:** `Nguyễn Tuấn Anh` (`@TuanAnhNg131`) kiêm Đóng gói, Bench/QA, Release/Integrator và Điều phối retro.

## Lát công việc & Acceptance Criteria

| Lát | Phạm vi & file chính | AC mục tiêu | Phụ thuộc |
|---|---|---|---|
| **Manifest v1.3, Bench & Soak** | `game.contract.json`, `chonoi/sim/day.py`, `chonoi/bench.py`, `chonoi/soak.py`, `tests/helpers.py` | `AC-P4-01` (`contract_version: "1.3"`, `bench_cmd` 1280×720 đo `30s` sau `3s` làm nóng), `AC-P4-02` (`soak_cmd` 10 ngày tất định, `crashes=0`) | Phase 3 |
| **Cảnh báo & Tiếp cận UI** | `chonoi/web/index.html` | `AC-P4-03` (3 cảnh báo Thủy quái / Oxy / Khách giận có chữ + icon, chế độ tương phản cao `H` và phụ đề SFX) | `AC-P4-01` |
| **QA & Đóng gói Clone sạch** | `tests/test_p4_release.py`, `docs/proof/phase-4/*`, `LICENSE`, `CREDITS.md` | `AC-P4-04` (Toàn bộ test P1–P4 xanh, chạy được từ clone sạch ≤ 3 lệnh), `AC-P4-05` (Đạt mốc bench & soak thật) | Lát 1–2 |
| **Retro, Phản tư & Release** | `docs/retro.md`, `docs/members/TuanAnhNg131.md`, `docs/release-v1.0.0.md`, `docs/verification/phase-4.md`, `CHANGELOG.md`, `README.md` | `AC-P4-06` (Rà hành động P2 ở retro P4 & phản tư ≤ 200 từ), `AC-P4-07` (Gói phát hành `v1.0.0` + tag `phase-4` & `v1.0.0`) | Lát 3 |
