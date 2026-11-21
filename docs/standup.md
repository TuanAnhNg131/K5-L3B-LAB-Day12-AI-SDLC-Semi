# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | `@TuanAnhNg131` | Kickoff `TEAM.md`, hợp đồng v1.0, luật `gather` và `quan`, validation `scenario.py` | Viết `tests/test_p1_rules.py`, sinh bằng chứng `docs/proof/phase-1/`, cập nhật ma trận truy vết và gắn tag `phase-1` | Không (đã xử lý Windows `python3` alias trong `tests/helpers.py`) |
| Phase 2 | `@TuanAnhNg131` | Contract v1.1, cá bơi/sinh, Cá Sấu Năm Chèo, `DaySim` + Shop, menu/pause/HUD + WebAudio | Chạy test P1–P2, sinh bằng chứng `docs/proof/phase-2/`, retro nhanh và gắn tag `phase-2` | Fixture `ca_loc` ở độ sâu `5 m` trong test P1 cần đặt `random_fish: false` |
| Phase 3 | `@TuanAnhNg131` | ADR-0001 tác động, kho cá thể `{id, kind, fresh}`, hao tươi `1/240`, giữ chỗ theo id, giá theo độ tươi, HUD `ƯƠN` | Chạy full test P1–P3, lưu bằng chứng `docs/proof/phase-3/`, cập nhật `CHANGELOG.md` và gắn tag `phase-3` | Không (toàn bộ `base_price` và round-trip ngưỡng 30 đều chính xác) |
