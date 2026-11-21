# Day 12 — AI SDLC: Quán Ăn Chợ Nổi (`v1.0.0` · Nhóm Semi)

> Game quản lý quán ăn 2D miền Tây Nam Bộ: buổi sáng Út Sen lặn bắt cá, hái rau trên sông Chín Khúc; tối mở quán phục vụ khách trên nhà bè của Má Tư.
> Nhóm `Semi` (`TuanAnhNg131` — nhóm 1 thành viên) · **Test Contract `v1.3`** · Giấy phép [`LICENSE`](LICENSE) · Bản phát hành [`docs/release-v1.0.0.md`](docs/release-v1.0.0.md).

## Chạy nhanh từ clone sạch (≤ 3 lệnh trên macOS / Linux)

**Yêu cầu môi trường:** Python `3.12+` (chỉ dùng thư viện chuẩn, không cần cài thêm gói ngoài) và trình duyệt hiện đại.

```bash
git clone https://github.com/TuanAnhNg131/K5-L3B-LAB-Day12-AI-SDLC-Semi.git && cd K5-L3B-LAB-Day12-AI-SDLC-Semi
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # chạy toàn bộ test P1-P4 (1 lệnh)
python3 -m chonoi.live --mode day --days 5                          # mở chơi trọn 5 ngày tại http://127.0.0.1:8000/
```

*(Trên Windows PowerShell dùng `python` thay `python3`; khi chạy `unittest` xóa biến proxy nếu máy bật proxy nội bộ: `$env:PYTHONPATH="tests;."; $env:http_proxy=""; $env:https_proxy=""; python -m unittest discover -s tests -v`.)*

## Điều khiển & Tính điểm

- **Di chuyển:** `WASD` hoặc phím mũi tên · **Tương tác (cập bến / hái rau / nấu / bưng / phục vụ):** `E`
- **Bắt cá (dưới nước):** `Space` · **Tạm dừng:** `Esc` hoặc `P` · **Tương phản cao:** `H` · **Chơi lại:** `R`
- **Trong Shop cuối ngày:** Phím `1` (Bình Oxy), `2` (Áo Phao), `Enter` (Xong Shop)
- **Cách tính điểm:** `score = earned + 100 * floor(reputation)` (`earned` tính bằng nghìn đồng gồm tiền món theo độ tươi + boa; mua nâng cấp chỉ trừ `money`).

## Các lệnh Headless, Benchmark & Soak (`game.contract.json` v1.3)

```bash
python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

- **Hợp đồng kho & độ tươi (`v1.2–v1.3`):** Xem [`docs/contracts/README.md`](docs/contracts/README.md), [`docs/adr/0001-itemized-inventory-freshness.md`](docs/adr/0001-itemized-inventory-freshness.md) và [`docs/contracts/inventory.sample.json`](docs/contracts/inventory.sample.json). Chi tiết khung kỹ thuật ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm giữ nguyên tuyệt đối toàn bộ quy tắc lõi và mở rộng ở lớp client (tắt hoàn toàn trong chế độ `headless` / `soak`):

### Sáng tạo của nhóm
- **Giao diện Chợ Nổi Miền Tây, Âm thanh WebAudio & Phụ đề SFX:** Vẽ trực quan sông phù sa, bờ dừa nước, nhà bè đèn dây vàng, Út Sen mặc áo bà ba/khăn rằn và kính lặn, hiệu ứng cảnh báo Thủy quái viền tím, nhạc nền ngũ cung + SFX tổng hợp bằng WebAudio API lưu âm lượng qua `localStorage`, kèm thanh phụ đề SFX và chế độ tương phản cao (`H`).
- **Bằng chứng lõi vẫn đúng:** Toàn bộ logic trong `chonoi/sim/*` độc lập với UI/SFX; toàn bộ 67/67 bài kiểm thử tự động hộp đen (`tests/test_smoke_p1.py`, `tests/test_p1_rules.py`, `tests/test_p2_rules.py`, `tests/test_p3_rules.py`, `tests/test_p4_release.py`), benchmark `30s` (`821.88 FPS`) và soak `10` Ngày (`crashes = 0`) đều đạt trên cùng commit bàn giao (xem [`docs/verification/phase-4.md`](docs/verification/phase-4.md)).

## Quy trình & Tài liệu nhóm (`Semi`)

- Thành viên & vai: [`TEAM.md`](TEAM.md) · Hướng dẫn AI: [`AGENTS.md`](AGENTS.md) · Phản tư cá nhân: [`docs/members/TuanAnhNg131.md`](docs/members/TuanAnhNg131.md)
- Kế hoạch & Kiểm chứng: `docs/plan/phase-1..4.md`, `docs/verification/phase-1..4.md`, bằng chứng thật tại `docs/proof/phase-1..4/`
- Nhật ký: [`docs/clarify.md`](docs/clarify.md) · [`docs/standup.md`](docs/standup.md) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md) · [`docs/retro.md`](docs/retro.md) · [`CHANGELOG.md`](CHANGELOG.md) · [`CREDITS.md`](CREDITS.md)
