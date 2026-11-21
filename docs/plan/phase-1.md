# Kế hoạch Phase 1 (PRD-0 · Test Contract v1.0)

- **Mục tiêu:** Hoàn thiện trọn vẹn lõi Phase 1 cho cả 2 chế độ `gather` và `quan` theo đúng Test Contract v1.0, nối qua file kho, đạt 100% smoke test, unit test và test quy tắc nghiệp vụ trước khi gắn tag `phase-1`.
- **Phân công:** Nhóm 1 thành viên `Nguyễn Tuấn Anh` (`@TuanAnhNg131`) kiêm PO, Integrator, QA Lead và Release, thực hiện tuần tự qua 4 lát công việc dưới sự hỗ trợ của AI.

## Kế hoạch theo lát & Acceptance Criteria (AC)

| Lát | Phạm vi & file chính | AC mục tiêu | Người làm | Phụ thuộc |
|---|---|---|---|---|
| **Kickoff & Contracts** | `TEAM.md`, `game.contract.json`, `tests/helpers.py`, `docs/contracts/README.md`, `.agents/skills/*`, `AGENTS.md` | `AC-P1-01` (Team & contract setup), `AC-P1-02` (Harness AI & hợp đồng tích hợp) | `TuanAnhNg131` | Không |
| **Lát 1 & 2 (`gather`)** | `chonoi/sim/gather.py` | `AC-P1-03` (Bơi, dive/surface, oxy, ngạt, ngất LIFO), `AC-P1-04` (Hái nút, mọc lại, bắt cá, cập bến, xuất kho nguyên tử) | `TuanAnhNg131` | `AC-P1-01` |
| **Lát 3 & 4 (`quan`) & Validation** | `chonoi/scenario.py`, `chonoi/sim/quan.py` | `AC-P1-05` (Scenario conflict -> mã 2), `AC-P1-06` (Lịch khách, giữ chỗ, `no_dish`), `AC-P1-07` (Bếp, bưng, phục vụ, boa, uy tín, đóng ca) | `TuanAnhNg131` | `AC-P1-02` |
| **QA, Tích hợp & Đóng gói P1** | `tests/test_p1_rules.py`, `docs/proof/phase-1/*`, `docs/verification/phase-1.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `CHANGELOG.md`, `README.md` | `AC-P1-08` (Smoke 2 tiến trình), `AC-P1-09` (Tất định byte-to-byte), `AC-P1-10` (Chơi thử live), `AC-P1-11` (DoD tài liệu & tag `phase-1`) | `TuanAnhNg131` | Lát 1–4 |

## Rủi ro & biện pháp
- **Sai thứ tự xử lý trong `step` hoặc sai ngưỡng biên (`tick 0`, `patience==0`, `choke` ở `t+59`):** Đối chiếu từng dòng mục E & F của PRD-0 và viết test hộp đen kiểm tra chính xác từng tick biên trong `tests/test_p1_rules.py`.
- **Lệnh `python3` trên Windows trỏ tới Store alias (`WinError 1920`) & proxy sandbox chặn localhost ở `test_live.py`:** Bổ sung fallback `sys.executable` trên Windows trong `tests/helpers.py` (giữ nguyên `game.contract.json` cho Linux/macOS) và làm sạch biến proxy khi chạy kiểm thử cục bộ.
