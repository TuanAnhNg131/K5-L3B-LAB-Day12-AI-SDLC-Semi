---
name: verify-contract
description: Chạy kiểm thử hợp đồng (Test Contract), kiểm tra tính tất định theo byte, mã thoát lỗi 2 và lưu bằng chứng chạy thật cho từng phase.
---

# Skill: Verify Test Contract

Dùng skill này mỗi khi hoàn thành một lát code hoặc trước khi gắn tag `phase-n`.

## Quy trình kiểm chứng

1. **Chạy toàn bộ bộ test (unit + black-box smoke + rule tests):**
   - Trên Linux/macOS:
     ```bash
     PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
     ```
   - Trên Windows PowerShell (lưu ý xóa proxy nếu test `LiveServerTest` gọi `127.0.0.1`):
     ```powershell
     $env:PYTHONPATH="tests;."; $env:http_proxy=""; $env:https_proxy=""; python -m unittest discover -s tests -v
     ```

2. **Kiểm tra smoke tích hợp hai tiến trình (buổi sáng -> file kho -> buổi tối):**
   - Chạy `gather` với `--inventory-out` ra file kho tạm và chạy `quan` với `--inventory` đọc đúng file đó.
   - Đảm bảo kiểm dữ liệu sai trả về mã thoát `2` và **không** tạo file `--out` hoặc `--inventory-out`.

3. **Kiểm tra tính tất định (Determinism):**
   - Chạy cùng `--mode`, `--seed`, `--scenario`, `--inputs`, `--ticks` hai lần và so sánh kết quả JSONL trùng khớp từng byte.

4. **Lưu bằng chứng thật:**
   - Lưu output chạy test và kết quả smoke test (JSONL / kho JSON) vào `docs/proof/phase-<n>/`.
   - Cập nhật ma trận truy vết `docs/verification/phase-<n>.md` dẫn đúng tới đường dẫn trong `docs/proof/phase-<n>/`.
