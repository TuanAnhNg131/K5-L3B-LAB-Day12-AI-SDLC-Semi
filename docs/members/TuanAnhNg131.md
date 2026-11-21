# TuanAnhNg131 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:** Thực hiện toàn bộ 4 phase cho nhóm `Semi` (`15` commit trên `main`, các tag `phase-1`..`phase-4` và `v1.0.0`): cài đặt luật `gather`/`quan` (`fc88ded`, `f46b21c`), nâng cấp v1.1 với cá bơi, Cá Sấu, chế độ `day`, Shop, `pause` & UI (`b1c14dc`, `3f57d1e`), chuyển đổi kho cá thể & độ tươi v1.2 (`c3c0a68`, `aaa0bed`), xây dựng `bench.py`, `soak.py`, 3 cảnh báo, tương phản cao và phụ đề SFX.
- **Tôi đã rà soát:** Kiểm tra diff trước mỗi commit, đối chiếu `docs/contracts/README.md`, `ADR-0001` và chạy `67/67` test hộp đen cùng kiểm thử từ clone sạch.
- **AI sai ở đâu & phát hiện:** Ở Phase 1, test nổi lên né ngạt fail vì thiếu `ramp_max_ticks = 6` ở tick đầu; ở Phase 3, `base_price` tick 1 bị hụt `1k` do bước `quan` hao tươi chạy trước `cook_started`. Đều phát hiện qua test hộp đen.
- **Bài học:** Chốt hợp đồng sớm, viết ADR trước breaking change và dùng số học chính xác (`1/240` + `Fraction`) giữ nhánh `main` luôn chạy được qua mọi phase.
