# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | `@TuanAnhNg131` | Antigravity AI | Kickoff `TEAM.md`, `game.contract.json`, `docs/contracts/README.md`, `docs/plan/phase-1.md`, tạo 2 skills trong `.agents/skills/` | ~12k tokens | Cần kiểm tra kỹ quy ước `headless_cmd` giữ `python3` cho Linux/macOS thay vì sửa thẳng sang `python` của Windows. |
| Phase 1 | `@TuanAnhNg131` | Antigravity AI | Cài đặt luật `gather` và `quan` (`chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/scenario.py`) và test `tests/test_p1_rules.py` | ~25k tokens | Rà soát lại điều kiện `tip` tránh sai số dấu phẩy động (`Decimal`) và đồng bộ `player.vel` trong snapshot `quan`. |
| Phase 2 | `@TuanAnhNg131` | Antigravity AI | Nâng cấp v1.1: `game.contract.json`, cá bơi/sinh, Cá Sấu Năm Chèo, `DaySim` & Shop, `pause`, validation, UI/WebAudio, `tests/test_p2_rules.py` | ~40k tokens | Phát hiện test P1 `ca_loc` tại `d=5` bị kẹp độ sâu khi bật cá bơi và bổ sung ghi file đầu ra nguyên tử ở `runner.py` để tránh tạo file rác khi `DaySim` báo mã `2` lúc chuyển pha. |
