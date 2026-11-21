# Release Notes — Quán Ăn Chợ Nổi `v1.0.0` (`phase-4`)

**Nhóm:** `Semi` (`TuanAnhNg131`) · **Test Contract:** `v1.3` · **Giấy phép:** MIT ([`LICENSE`](../LICENSE))

## Điểm mới & Tính năng hoàn chỉnh
1. **Lặn & Hái (`gather`, Contract v1.3):** Mặt cắt sông 2D với 6 nút hái (`N1–N6`: bông điên điển, bông súng, kèo nèo), 3 loài cá bơi/đổi hướng/phản xạ biên/sinh mới (`cá linh`, `cá lóc`, `cá kèo`), Cá Sấu Năm Chèo (`M1` từ Ngày 1, `M2` từ Ngày 3) với tuần tra/rượt đuổi/chạm mất giỏ LIFO/`recoil`, oxy & ngạt thở, cập bến và xuất file kho nguyên tử.
2. **Mở Quán (`quan`):** 2 bếp (`B1–B2`), 4 bàn (`T1–T4`), 6 món thực đơn Nam Bộ, giữ chỗ theo `id` cá thể tươi nhất, nấu/bưng/phục vụ/boa/uy tín và đóng ca.
3. **Vòng Ngày & Độ Tươi (`day`, Shop):** Chu trình `DayIntro → gather → EveningIntro → quan → DayResult → Shop → Summary` xuyên 5 Ngày; nâng cấp bình oxy & áo phao; kho cá thể `{id, kind, fresh}` với đơn vị `1/240` + `Fraction` chính xác tại ngưỡng `30` (`spoiled`), thử giữ lại 1 lần khi ươn và giá món tính theo độ tươi.
4. **Hiệu năng, Tiếp cận & Sáng tạo:**
   - Benchmark render `1280×720` (`chonoi.bench`): **821.88 FPS** trung bình, **280.21 FPS** 1% low, **177.24 ms** thời gian nạp (đo `30s` sau `3s` làm nóng).
   - Soak headless `10` Ngày (`chonoi.soak`): hoàn thành **10/10** Ngày, **0** crash, tất định 100%.
   - 3 cảnh báo rõ chữ + biểu tượng (*Thủy quái gần*, *Oxy sắp hết / Hết hơi*, *Khách sắp giận*), **chế độ tương phản cao (`H`)**, **phụ đề SFX**, giao diện chợ nổi + nhạc nền/SFX WebAudio (lưu âm lượng `localStorage`).

## Cách chạy từ gói phát hành / clone sạch
Yêu cầu: Python 3.12+ (chỉ thư viện chuẩn, không cần `pip install`) và trình duyệt hiện đại.
```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode day --days 5
```

## Giới hạn đã biết
- Không bật các mục mở rộng tùy chọn (`weapon`, `net`, `snake`, `burn`, `vendor`, `ca_ho`, `current`, `reservations`, `leaderboard`: `"extensions": []`), do nhóm 1 thành viên ưu tiên hoàn thiện 100% lõi Contract v1.0–v1.3 và kiểm chứng chặt chẽ.
- `tools/check_team.py` giữ điều kiện mẫu `4..6` thành viên theo quy định chung của lớp (CI chỉ cảnh báo, không chặn).
