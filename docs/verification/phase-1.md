# Ma trận truy vết Phase 1 (PRD-0 · Test Contract v1.0)

| AC | Mô tả yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| `AC-P1-01` | Thiết lập nhóm `Semi`, `TEAM.md` (`team_size: 1`), `game.contract.json` v1.0 | Kiểm tra thủ công + `tests/test_team_check.py` | [`TEAM.md`](../../TEAM.md), [`game.contract.json`](../../game.contract.json), [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-02` | Hợp đồng tích hợp kho/sự kiện & 2 skills nhóm + cập nhật `AGENTS.md` | Rà soát file hợp đồng & skill | [`docs/contracts/README.md`](../contracts/README.md), [`.agents/skills/verify-contract/SKILL.md`](../../.agents/skills/verify-contract/SKILL.md), [`.agents/skills/phase-release/SKILL.md`](../../.agents/skills/phase-release/SKILL.md) | Đạt |
| `AC-P1-03` | `gather`: bơi, chặn biên, `dive`/`surface`, oxy, ngạt đúng `t+59`, ngất bỏ giỏ LIFO + kho rỗng | Test hộp đen (`test_smoke_p1.py`, `test_p1_rules.py`) | [`tests/test_p1_rules.py`](../../tests/test_p1_rules.py), [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-04` | `gather`: hái nút ở mặt nước, mọc lại, bắt cá + cooldown + `hold_full`, ưu tiên cập bến | Test hộp đen (`test_p1_rules.py`) | [`tests/test_p1_rules.py`](../../tests/test_p1_rules.py), [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-05` | Từ chối đầu vào/scenario sai hoặc mâu thuẫn bằng mã thoát `2` trước khi ghi file đầu ra | Test hộp đen (`test_con_03_*`, `test_invalid_quan_scenarios_exit_2_without_output`) | [`tests/test_smoke_p1.py`](../../tests/test_smoke_p1.py), [`tests/test_p1_rules.py`](../../tests/test_p1_rules.py), [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-06` | `quan`: lịch khách theo `phase_tick`, giữ chỗ công thức, `no_dish` khi hết nguyên liệu | Test hộp đen (`test_customer_schedule_and_no_dish`) | [`tests/test_p1_rules.py`](../../tests/test_p1_rules.py), [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-07` | `quan`: chọn `interact` `(khoảng cách, bếp trước bàn, id)`, nấu/nhặt/phục vụ, boa, uy tín, đóng ca, tính điểm | Test hộp đen (`TestQuanRules.*`) | [`tests/test_p1_rules.py`](../../tests/test_p1_rules.py), [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-08` | Smoke hai tiến trình `gather --inventory-out` → `quan --inventory` | Chạy thật 2 lệnh headless + `test_inv_01_*` | [`smoke-gather.jsonl`](../proof/phase-1/smoke-gather.jsonl), [`smoke-catch.json`](../proof/phase-1/smoke-catch.json), [`smoke-quan.jsonl`](../proof/phase-1/smoke-quan.jsonl) | Đạt |
| `AC-P1-09` | Tính tất định theo byte cho cả `gather` và `quan` | `test_con_02_deterministic_bytes`, `test_quan_deterministic_bytes` | [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-10` | Chơi thử trực tiếp trên trình duyệt qua `chonoi.live` | `tests/test_live.py` + `tests/test_python_starter_units.py` | [`test-output.txt`](../proof/phase-1/test-output.txt) | Đạt |
| `AC-P1-11` | Hoàn thiện `README.md`, `CHANGELOG.md`, `clarify.md`, `ai-usage-log.md`, `standup.md`, tag `phase-1` | Rà DoD Phase 1 và kiểm tra `git status`/`git tag` | [`README.md`](../../README.md), [`CHANGELOG.md`](../../CHANGELOG.md), [`docs/plan/phase-1.md`](../plan/phase-1.md) | Đạt |

## Đánh giá ngắn
- **Yêu cầu đạt:** Toàn bộ 46/46 test (khung + smoke hộp đen + test luật Phase 1 + live server + team check) đều xanh (`OK`). Smoke hai tiến trình truyền kho `{"items":{"bong_sung":2,"ca_loc":1}}` từ `gather` sang `quan` khớp chính xác tại tick `0`.
- **Yêu cầu chưa đạt:** `tools/check_team.py` mặc định yêu cầu 4–6 thành viên theo mẫu lớp, nhưng nhóm thực tế là nhóm 1 người (`team_size: 1`, đã ghi nhận trong `docs/clarify.md`).
- **Điều cần chỉnh cho phase sau:** Chuẩn bị nâng cấp lên Test Contract v1.1 ở Phase 2 (`--mode day`, cá bơi & sinh cá, Cá Sấu Năm Chèo, 2 bếp 4 bàn 6 món, Shop nâng cấp, menu/pause/HUD).
