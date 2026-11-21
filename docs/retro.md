# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Chuyển đổi từ Contract v1.0 sang v1.1 mạch lạc; toàn bộ logic `gather` (cá bơi/sinh, Cá Sấu) và `quan` tái sử dụng trực tiếp trong `DaySim` mà không nhân đôi code giữa headless và `chonoi.live`.
- Điều tệ: Một vài fixture test cũ của Phase 1 (`test_catch_underwater...` có `ca_loc` ở độ sâu `5 m` trong khi chuẩn mới quy định `ca_loc` bơi `[8, 20]`, và quán mở rộng lên 4 bàn) bị ảnh hưởng khi bật số chuẩn nên phải điều chỉnh rõ lý do trong test.
- 1 hành động cho Phase 3 (`TuanAnhNg131`): Trước khi sửa schema ở Phase 3 (đổi kho đếm sang kho cá thể), viết bảng phân tích tác động & ADR trước để kiểm soát toàn bộ điểm chạm ở `inventory`, `gather`, `quan`, `day` và `scenario`.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
