# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Nhóm chỉ có 1 thành viên (`Nguyễn Tuấn Anh`, `@TuanAnhNg131`), xử lý `TEAM.md` và `team_size` thế nào? | Ghi 1 dòng thành viên thật trong `TEAM.md` và đặt `"team": "Semi"`, `"team_size": 1` trong `game.contract.json`. Trong CI, `tools/check_team.py` chỉ cảnh báo (`continue-on-error: true`). | TuanAnhNg131 |
| 2 | 2026-11-21 | Trên Windows, `python3` trỏ tới Microsoft Store stub (`WinError 1920`) khi `tests/helpers.py` gọi `headless_cmd`. | Giữ nguyên `"headless_cmd": "python3 -m chonoi.headless"` trong `game.contract.json` cho CI Linux/macOS; bổ sung fallback sang `sys.executable` chỉ khi `os.name == "nt"` trong `tests/helpers.py`. | TuanAnhNg131 |
| 3 | 2026-11-21 | Thứ tự xử lý khi ở đúng tick cuối (`time_left_ticks == 1` -> `0`) của `gather` và `quan`? | `gather`: xét `interact` (bến trước hái) và `catch` trong bước đó trước khi chốt `time` (trừ khi đã `fainted` hoặc `docked`). `quan`: xét `served` ở bước 3 trước khi chốt khách `eating` trả tiền (`closing`) và khách `waiting` rời (`closing`, không phạt uy tín) ở bước 4. | TuanAnhNg131 (theo PRD-0 mục F) |
| 4 | 2026-11-21 | Đối tượng gần nhất trong `interact` ở `quan` không tương tác được (vd bàn trống gần hơn bếp sẵn sàng) có xét đối tượng kế tiếp không? | Không: chọn đúng 1 đối tượng theo `(khoảng cách, bếp trước bàn, id)`; nếu không tương tác được thì bỏ lượt. | TuanAnhNg131 (theo PRD-0 mục F) |
