# Hướng dẫn vận hành Quant V34

Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư. Cấu trúc lõi: mua đều E1VFVN30 hằng tháng cộng luật tạm dừng khi VN-Index dưới MA200; danh sách mã chất lượng chỉ để theo dõi. Kết quả backtest và lý do nằm ở `docs/BAO_CAO_DANH_GIA_V34.md` và `docs/NHAT_KY_BACKTEST.md`.

## 1. Việc bạn cần làm một lần (sau khi xem và merge pull request)

1. **Merge PR #2 vào `main`.** Chỉ sau khi merge, các lịch chạy mới có hiệu lực (GitHub chỉ chạy lịch từ nhánh mặc định) và hook khởi động phiên áp dụng cho mọi phiên Claude Code.
2. **Secrets** (Settings → Secrets and variables → Actions). Đã có từ V33: `GEMINI_API_KEY`, `EMAIL_USER`, `EMAIL_PASS`. Thêm nếu muốn: `EMAIL_NHAN` (danh sách người nhận, cách nhau bằng dấu phẩy; không đặt thì mail gửi đến `EMAIL_USER`).
3. **Vị thế (tùy chọn):** đổi tên `data/vi_the.mau.json` thành `data/vi_the.json` và khai số thật (`tien_mat` bằng đồng; `co_phieu` là số lượng). Báo cáo sẽ có bảng vị thế và tỷ lệ tiền mặt.
4. **Chạy tay một lần** workflow `Run Quant V34 Daily` (Actions → Run workflow) để kiểm tra mail trước khi để lịch tự chạy.

## 2. Dữ liệu bạn có thể bổ sung (CSV, không bắt buộc)

Chưa có file thì phép thử tương ứng ghi "không đánh giá được", không tự gán "đạt". Mẫu nằm ở `data/*.mau.csv`; đổi tên bỏ `.mau`.

| File | Cột | Dùng cho |
| --- | --- | --- |
| `data/lai_suat_lnh.csv` | `ngay`, `lai_suat_qua_dem_pct` (theo tuần, từ 2015) | Tầng 3: tạm dừng mua khi lãi suất qua đêm (trung bình 4 tuần) tăng từ 1 điểm % trở lên so với 13 tuần trước |
| `data/kiem_toan_y_kien.csv` | `ma`, `nam`, `y_kien` (`chấp nhận toàn phần`, `ngoại trừ`, `từ chối`, `không thể đưa ra ý kiến`) | Bộ lọc: loại mã có ý kiến ngoại trừ hoặc từ chối trong 3 năm tài chính gần nhất |
| `data/cam_co.csv` | `ma`, `ngay`, `ty_le_pct` (% cổ phần lưu hành bị cầm cố) | Bộ lọc: loại mã có tỷ lệ cầm cố mới nhất (12 tháng) từ 30% trở lên |

Chạy thử tác động của lãi suất: `python v34/chay_tang3_mo_rong.py` (thêm luật `("lai_suat", ...)` vào danh sách `RULES`).

## 3. Các workflow

| Workflow | Khi nào chạy | Việc làm |
| --- | --- | --- |
| `run_quant_v34.yml` | Thứ Hai đến thứ Sáu, 16:00 giờ Việt Nam | Chạy kiểm thử, cập nhật giá, lập báo cáo, gửi mail (tự bỏ qua ngày không có phiên) |
| `cap_nhat_bctc_v34.yml` | Hằng ngày 10:00 | Hỏi 1 lệnh kết quả kinh doanh cho mỗi mã; chỉ tải lại khi có kỳ mới; phát hiện mã chậm công bố |
| `lam_moi_du_lieu_v34.yml` | Ngày 5 hằng tháng | Làm mới BCTC năm và cổ tức (CafeF), hồ sơ ngành |
| `tai_du_lieu_v34.yml` | Chạy tay | Tải lại toàn bộ BCTC và dữ liệu mở rộng (Vietcap) |
| `tai_ds_lon_v34.yml` | Chạy tay | Tải toàn bộ mã HSX, HNX và mã đã hủy niêm yết, 6 luồng song song |
| `kiem_thu_mail_v34.yml` | Chạy tay | Gửi một mail kiểm thử thật (tiêu đề có `[KIEM THU]`) và gọi Gemini thật |
| `kiem_bao_cao_v34.yml` | Chạy tay | Chạy báo cáo trên runner, không gửi mail |
| `run_quant.yml` (V33) | Chạy tay | Giữ để tham chiếu; đã bỏ lịch chạy |

Mỗi workflow có thể chạy tay: Actions → chọn workflow → Run workflow.

## 4. Kiểm thử

```
python -m unittest discover -s tests -v      # 11 kiểm thử, khoảng 6 giây, không cần mạng
```
Gồm: bảo toàn giá trị, phí và thuế, T+2,5, giá trần chặn mua, không nhìn trước BCTC và dữ liệu nội bộ, nhập được mọi module, và logic ba luồng nhập tay. Workflow hằng ngày chạy bộ kiểm thử này trước khi lập báo cáo; kiểm thử lỗi thì báo cáo không chạy.

Chạy thử báo cáo không mạng và không gửi mail:
```
python v34/bao_cao_v34.py --khong-gui --khong-mang --bo-qua-kiem-tra-phien
```

## 5. Cấu trúc thư mục

- `v34/`: mã nguồn. `khung_backtest.py` (khung dùng chung), `tang2_*`, `du_lieu_dai.py` (bộ lọc mẫu dài), `tang3_*`, `tang4_wyckoff.py`, `bao_cao_v34.py` (báo cáo), `cap_nhat_bctc.py`, `tai_*.py` (tải dữ liệu).
- `data/`: dữ liệu (giá, BCTC, cổ tức, giao dịch nội bộ, hồ sơ ngành). Đã nén gọn.
- `docs/ket_qua_*.txt`: kết quả thô từng lần chạy backtest.
- `tests/`: kiểm thử tự động.
- `.claude/`: hook khởi động phiên cho Claude Code trên cloud.

## 6. Xử lý sự cố

- **Mail không đến:** chạy `kiem_thu_mail_v34.yml`, xem log bước chạy báo cáo ("Đã gửi" hoặc "Lỗi gửi"). Gmail cần mật khẩu ứng dụng cho `EMAIL_PASS`.
- **Không có lời bình:** thiếu hoặc sai `GEMINI_API_KEY`; báo cáo vẫn đủ bảng, chỉ thiếu phần lời bình.
- **Báo cáo báo "chậm công bố":** một mã đã quá hạn nộp BCTC (quý +45 ngày, năm +90 ngày) mà dữ liệu chưa có. Chậm nộp tự nó là dấu hiệu cảnh báo; kiểm tra thủ công trước khi tin danh sách chất lượng.
- **Nguồn dữ liệu bị chặn hoặc đổi:** hai nguồn (Vietcap IQ, CafeF) là API không chính thức, có thể đổi bất kỳ lúc nào. Script dừng ngay khi gặp mã 403 hoặc 429 và không cố vượt chặn. Cách bền hơn: nguồn chính thức có khóa API (DNSE Lightspeed, SSI FastConnect) và thay các hàm `tai_*`.
- **Năm 2015 thiếu ở một số công ty:** lỗi của nguồn CafeF (dữ liệu quý cũng thiếu); bộ lọc dùng các năm có sẵn.

## 7. Giới hạn cần nhớ

- Không có nguồn tự động cho lãi suất liên ngân hàng, ý kiến kiểm toán thật và cầm cố cổ phiếu (xem mục 2).
- Backtest dùng giá đã điều chỉnh; chuẩn VN-Index giả lập không có cổ tức, nên so sánh dùng thêm phiên bản cộng 2,2%/năm (ước lượng).
- Kết quả tầng 2 chưa có ý nghĩa thống kê rõ rệt; đây là danh sách theo dõi chứ không phải khuyến nghị mua.
