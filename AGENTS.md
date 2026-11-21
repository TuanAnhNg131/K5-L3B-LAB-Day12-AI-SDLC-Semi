# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test (Linux/macOS): `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Test (Windows PowerShell): `$env:PYTHONPATH="tests;."; $env:http_proxy=""; $env:https_proxy=""; python -m unittest discover -s tests -v`
- Headless: `python -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl` (trên Linux/macOS dùng `python3`)
- Benchmark (`1280×720`): `python -m chonoi.bench --seed 42 --duration 30 --out bench.json`
- Soak (`10` ngày): `python -m chonoi.soak --seed 7 --days 10 --out soak.json`
- Chơi thử trên trình duyệt: `python -m chonoi.live --mode day --days 5` (mở địa chỉ in ra; WASD, E, Space, Esc/P, H tương phản cao, R)

## Trạng thái Phase & quy ước cập nhật
- **Phase 4 (Test Contract v1.3 · Release `v1.0.0`):** `Semi` (`TuanAnhNg131`). Hoàn tất toàn bộ 4 phase: thêm `bench_cmd`, `soak_cmd`, 3 cảnh báo dễ nhận biết + chế độ tương phản cao (`H`) + phụ đề SFX, đóng gói và phát hành `v1.0.0`. Xem [`docs/release-v1.0.0.md`](docs/release-v1.0.0.md).

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `.agents/skills/verify-contract/SKILL.md`: chạy kiểm thử hợp đồng, kiểm tra tính tất định từng byte, mã thoát `2`, smoke hai tiến trình và lưu bằng chứng vào `docs/proof/phase-<n>/`. Dùng sau khi xong mỗi lát hoặc trước khi chốt phase.
- `.agents/skills/phase-release/SKILL.md`: rà soát DoD, kiểm tra tài liệu bắt buộc (`verification`, `clarify`, `ai-usage-log`, `CHANGELOG`, `README`) trước khi commit và gắn tag `phase-<n>`. Dùng ở cuối mỗi phase.
