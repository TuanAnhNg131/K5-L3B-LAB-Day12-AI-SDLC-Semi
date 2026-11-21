---
name: phase-release
description: Rà soát Definition of Done (DoD), cập nhật tài liệu bắt buộc và thực hiện commit/tag chuẩn cho mỗi mốc phase-n.
---

# Skill: Phase Release Checklist

Dùng skill này ở cuối mỗi phase trước khi gắn tag `phase-n` (hoặc Release `v1.0.0` ở Phase 4).

## Checklist bắt buộc trước khi tag

1. **Mã nguồn & kiểm thử:**
   - Không còn `TODO(nhóm)` của phase hiện tại chưa xử lý.
   - Tất cả test (`tests/*.py`) chạy xanh 100% trên commit bàn giao.
   - `git status` không chứa file rác, file nháp hoặc thông tin bí mật (`.env`, API key). Không commit file ngoài phạm vi repo (`phase.md`, `.vscode/`).

2. **Tài liệu & bằng chứng:**
   - `docs/plan/phase-<n>.md`: đã ghi mục tiêu, phân công, AC và rủi ro.
   - `docs/verification/phase-<n>.md`: có đầy đủ bảng `AC -> cách kiểm chứng -> bằng chứng -> kết quả`.
   - `docs/proof/phase-<n>/`: có artifact chạy thật từ phiên bản code hiện tại.
   - `docs/clarify.md`, `docs/standup.md`, `docs/ai-usage-log.md`: đã cập nhật cho phase hiện tại.
   - `CHANGELOG.md` và `AGENTS.md`: phản ánh đúng thay đổi của phase.
   - `README.md`: lệnh cài đặt/chạy từ clone sạch (<= 3 lệnh trên macOS/Linux), điều khiển, tính điểm, lệnh test đều chính xác.

3. **Commit & Annotated Tag:**
   - Stage tường minh các file liên quan, viết commit message rõ ràng theo lát/tính năng.
   - Chạy lại bộ test một lần cuối sau commit cuối cùng.
   - Gắn annotated tag trên `main`:
     ```bash
     git tag -a phase-<n> -m "Phase <n>: mô tả ngắn gọn trạng thái đã kiểm chứng"
     ```
