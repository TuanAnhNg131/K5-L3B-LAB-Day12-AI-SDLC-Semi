# Ma trận truy vết Phase 4 (TICKET-04 · Test Contract v1.3 & Release v1.0.0)

| AC | Mô tả yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| `AC-P4-01` | `contract_version: "1.3"`, khai báo `bench_cmd`, chạy cảnh lặn `1280×720` (`3s` warmup + `30s` đo) xuất đúng 5 trường `bench.json` | Chạy `python -m chonoi.bench --seed 42 --duration 30` + `test_bench_cmd_schema_and_bad_args_exit_2` | [`bench.json`](../proof/phase-4/bench.json), [`test-output.txt`](../proof/phase-4/test-output.txt) | Đạt (`avg_fps=821.88`, `p1_low_fps=280.21`, `load_ms=177.24`) |
| `AC-P4-02` | `soak_cmd`: chạy `10` Ngày liên tục bằng bot tất định, lặp D1–D5 cho Ngày 6–10, `crashes = 0`, tất định | Chạy `python -m chonoi.soak --seed 7 --days 10` + `test_soak_cmd_10_days_deterministic_and_zero_crashes` | [`soak.json`](../proof/phase-4/soak.json), [`test-output.txt`](../proof/phase-4/test-output.txt) | Đạt (`10/10` ngày, `crashes=0`, `duration_s=6.853`) |
| `AC-P4-03` | 3 cảnh báo dễ nhận biết (Thủy quái, Oxy sắp hết/Hết hơi, Khách sắp giận), chế độ tương phản cao (`H`) và phụ đề SFX | Rà soát `chonoi/web/index.html` + `test_ui_accessibility_warnings_high_contrast_and_subtitles` | [`chonoi/web/index.html`](../../chonoi/web/index.html), [`test-output.txt`](../proof/phase-4/test-output.txt) | Đạt |
| `AC-P4-04` | Từ clone sạch chạy được bản giao diện & kiểm thử trong ≤ 3 lệnh; đủ `LICENSE` và `CREDITS.md` | Clone sạch sang thư mục tạm và chạy `unittest discover -s tests -v` | [`clean-clone-test.txt`](../proof/phase-4/clean-clone-test.txt), [`README.md`](../../README.md), [`LICENSE`](../../LICENSE), [`CREDITS.md`](../../CREDITS.md) | Đạt (`67/67 OK`) |
| `AC-P4-05` | Regression toàn bộ P1–P3 còn hiệu lực + test Phase 4 xanh 100% | Chạy toàn bộ 67 test trên nhánh `main` | [`test-output.txt`](../proof/phase-4/test-output.txt) | Đạt (`67/67 OK`) |
| `AC-P4-06` | Retro cuối rà lại hành động P2, số liệu commit/token, lỗi AI và phản tư cá nhân `≤ 200` từ | Rà `docs/retro.md`, `docs/members/TuanAnhNg131.md` (`186` từ) | [`docs/retro.md`](../retro.md), [`docs/members/TuanAnhNg131.md`](../members/TuanAnhNg131.md) | Đạt |
| `AC-P4-07` | `CHANGELOG.md`, release notes `v1.0.0`, đóng gói zip sạch, tag `phase-4` và `v1.0.0` cùng trỏ tới commit cuối trên `main` | Kiểm tra `git tag`, `git archive`, `docs/release-v1.0.0.md` | [`docs/release-v1.0.0.md`](../release-v1.0.0.md), [`CHANGELOG.md`](../../CHANGELOG.md) | Đạt |

## Đánh giá ngắn
- **Yêu cầu đạt:** Toàn bộ 67/67 bài kiểm thử P1–P4 (cả trên repo chính lẫn từ clean clone), benchmark `1280×720` (`821.88 FPS`, `1% low 280.21 FPS`, `load 177.24 ms`) và soak `10` Ngày (`10/10` ngày, `0` crash) đều đạt vượt chuẩn.
- **Lưu ý triển khai:** Kết thúc đủ 4 phase đúng quy trình; tệp đóng gói `release/quan-an-cho-noi-v1.0.0.zip` đã được tạo từ tag `v1.0.0` để sẵn sàng tải lên GitHub Release.
