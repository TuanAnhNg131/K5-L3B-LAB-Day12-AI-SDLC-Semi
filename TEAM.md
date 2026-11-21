# TEAM

**Tên nhóm:** Semi  **Số người:** 1  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Nguyễn Tuấn Anh | @TuanAnhNg131 | sim/gather, sim/quan, client/ui, qa | PO / Integrator / QA / Release | — (nhóm 1 người) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Nhóm 1 thành viên (`TuanAnhNg131`), làm việc trực tiếp trên repo chung cùng trợ lý AI.
- Khi bất đồng về thiết kế: Đối chiếu PRD/Test Contract và ghi giả định vào `docs/clarify.md` (hoặc ADR khi đổi schema).
- Khi vướng quá 10 phút: Tách nhỏ lát việc, kiểm tra lại contract/test trước khi viết tiếp luật chơi.
- Standup giữa phase: Tự rà lại checklist DoD và tiến độ từng lát ở phút 20 mỗi phase trong `docs/standup.md`.
- Cách đọc/rà code: Self-review diff, chạy toàn bộ unit test và smoke test hộp đen trước mỗi commit/tag.
- Cách làm việc với Git: Commit nguyên tử (atomic) trên nhánh `main` theo từng lát rõ ràng, chỉ gắn tag `phase-n` khi test xanh 100%.
- Khóa hợp đồng: Không tự ý sửa schema kho hay `game.contract.json` ngoài yêu cầu phase mà chưa cập nhật `docs/contracts/` và `CHANGELOG.md`.
