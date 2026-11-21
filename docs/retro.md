# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Chuyển đổi từ Contract v1.0 sang v1.1 mạch lạc; toàn bộ logic `gather` (cá bơi/sinh, Cá Sấu) và `quan` tái sử dụng trực tiếp trong `DaySim` mà không nhân đôi code giữa headless và `chonoi.live`.
- Điều tệ: Một vài fixture test cũ của Phase 1 (`test_catch_underwater...` có `ca_loc` ở độ sâu `5 m` trong khi chuẩn mới quy định `ca_loc` bơi `[8, 20]`, và quán mở rộng lên 4 bàn) bị ảnh hưởng khi bật số chuẩn nên phải điều chỉnh rõ lý do trong test.
- 1 hành động cho Phase 3 (`TuanAnhNg131`): Trước khi sửa schema ở Phase 3 (đổi kho đếm sang kho cá thể), viết bảng phân tích tác động & ADR trước để kiểm soát toàn bộ điểm chạm ở `inventory`, `gather`, `quan`, `day` và `scenario`.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2:** Đã thực hiện đầy đủ ngay đầu Phase 3 thông qua [`docs/adr/0001-itemized-inventory-freshness.md`](adr/0001-itemized-inventory-freshness.md), lập bảng tác động 6 module và migrate tuần tự từ tầng dữ liệu (`inventory`, `contract`, `scenario`) lên mô phỏng và test, nhờ vậy không gặp vỡ tích hợp hay lỗi ngoài dự kiến.
- **Điều tốt:** Toàn bộ `67/67` test P1–P4 chạy xanh; tách biệt sạch lõi mô phỏng tất định khỏi phần đồ họa/âm thanh UI; kết quả benchmark `1280×720` đạt `821.88 FPS` (`1% low 280.21 FPS`, `load 177.24 ms`) và soak `10` Ngày đạt `10/10` Ngày với `0` crash.
- **Điều cần sửa / hạn chế:** Nhóm 1 người nên không triển khai thêm các extension ngoài lõi (`weapon`, `net`, `burn`...), và trên Windows gặp hiện tượng `python3` trỏ tới Microsoft Store stub nên cần fallback `sys.executable` trong `tests/helpers.py`.
- **Số liệu:**
  - Số commit trên `main`: `TuanAnhNg131` = **15 commit** có nội dung xuyên suốt 4 phase (Phase 1: 4, Phase 2: 4, Phase 3: 4, Phase 4: 3).
  - Cách rà code: Tự review toàn bộ diff trước mỗi commit, chạy `verify-contract` (unit + hộp đen + tất định theo byte + kiểm thử clone sạch) và đối chiếu từng dòng với Test Contract.
  - Token ước tính: ~`143k` tokens (`TuanAnhNg131` qua Antigravity AI: P1 ~37k, P2 ~40k, P3 ~38k, P4 ~28k).
- **Một lần AI sai và cách phát hiện:** Ở Phase 1, test `test_oxygen_empty_choke_timing_and_surface_save` đặt người chơi tại `d = 0.6 m` để nổi lên trong `1` tick nhưng AI quên mất `ramp_max_ticks = 6` làm vận tốc tick đầu chỉ đạt `-0.667 m/s` nên người chơi chưa kịp qua `d <= 0.5` và vẫn bị `choke`. Lỗi được phát hiện ngay khi chạy bộ test hộp đen và sửa bằng cách thiết lập `pos: [20, 0.52], vel: [0, -4.0]`; tương tự ở Phase 3, tự kiểm tra ngay phép nhân `floor` với `fresh` giảm `1/240` ở tick 1 của `quan`.
- **Nếu làm lại, đổi gì:** Viết sẵn bộ fixture scenario biên (`ramp`, `tick cuối`, ngưỡng `30 ± 1/240`) ngay lúc kickoff để kiểm chứng nhanh hơn khi chuyển phase.
