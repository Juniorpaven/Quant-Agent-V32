# Nhật ký backtest V34

Mỗi lần chạy ghi: ngày, tầng, tham số, kết quả (CAGR, MDD, Sharpe, vòng quay, chi phí), so với mua đều E1VFVN30, quyết định.

## 27/11/2026
- Lập kế hoạch. Chưa chạy backtest.
- Bước tiếp theo: viết workflow tải dữ liệu vào data/, sau đó viết khung backtest.

## 27/11/2026 – Dữ liệu và tầng 3 (luật VN-Index so với MA200)

### Dữ liệu
- Run "Tai du lieu V34" #1 bị treo hơn 55 phút nên đã hủy. Sửa script (kiểm tra kết nối trước, timeout 10 giây, ghi log) rồi chạy lại #2.
- Giá Entrade tải được trên runner: 76 file CSV trong `data/gia/`, từ 2015-01-05 đến 2026-11-27 (một số mã niêm yết muộn hơn).
- **TCBS trả HTTP 403 (trang "Just a moment…" của Cloudflare) cho toàn bộ 761 lệnh gọi từ runner.** Chưa có BCTC và cổ tức, nên chưa làm được tầng 2.
- Hệ quả cho V33: bộ lọc OCF gọi TCBS bị 403 và âm thầm rơi sang yfinance, đúng điểm nghi ở mục 3.5 của kế hoạch, và trường hợp này nặng hơn dự đoán.
- Không dùng cách giả header hay Referer để vượt chặn của Cloudflare. Cần người dùng chọn nguồn BCTC khác (xem cuối mục).

### Chuẩn so sánh và tầng 3
Giả định: nạp 10 triệu đồng/tháng, phí 0,15%/chiều, thuế bán 0,1%, T+2,5, biên độ ±7%, lô 100, khớp ở giá mở cửa phiên sau. Lõi tạm dùng E1VFVN30 (chưa có tầng 2). Giá chưa điều chỉnh cổ tức (E1VFVN30 có chia cổ tức tiền mặt nhỏ nên số CAGR có thể thấp hơn thực tế).
Biến thể "ban_mua": dưới MA thì hạ lõi về 50% NAV (có bán). Biến thể "tam_dung": dưới MA thì không mua thêm, không bán. Đánh giá hằng tuần.

| Giai đoạn | Chiến lược | CAGR | MDD | Vòng quay bán/năm | Chi phí (triệu) |
| --- | --- | --- | --- | --- | --- |
| 2015–nay | Mua đều E1VFVN30 | 10,85% | −47,69% | 0% | 2,14 |
| 2015–nay | MA200 ban_mua 50% | 11,24% | −38,66% | 100,1% | 58,02 |
| 2015–nay | MA200 tam_dung | 10,74% | −47,27% | 0% | 2,11 |
| 2015–2020 (tối ưu) | Mua đều E1VFVN30 | 12,99% | −47,69% | 0% | 1,08 |
| 2015–2020 (tối ưu) | MA200 ban_mua 50% | 12,51% | −38,66% | 91,0% | 10,99 |
| 2015–2020 (tối ưu) | MA200 tam_dung | 12,43% | −47,27% | 0% | 1,08 |
| 2021–nay (kiểm tra) | Mua đều E1VFVN30 | 9,72% | −42,19% | 0% | 1,06 |
| 2021–nay (kiểm tra) | MA200 ban_mua 50% | 8,65% | −25,97% | 117,9% | 12,40 |
| 2021–nay (kiểm tra) | MA200 tam_dung | 9,81% | −34,28% | 0% | 1,03 |

Các cửa sổ MA150 và MA250 cho kết quả tương tự (xem chạy `python v34/chay_tang3.py`). Tham chiếu mua đều VN-Index không phí: 8,70% (2015–nay).

### Quyết định
- "ban_mua": **loại.** CAGR thấp hơn mua đều ở đoạn kiểm tra (8,65% so với 9,72%), vòng quay ~100–118%/năm vượt giới hạn 100% và phí cao. MDD tốt hơn nhưng không bù được.
- "tam_dung" MA200: **giữ tạm, chưa đạt rõ ràng.** CAGR ≈ chuẩn (−0,11 điểm cả giai đoạn, +0,09 điểm ở đoạn kiểm tra), vòng quay 0%. MDD chỉ cải thiện ở đoạn 2021–nay (−34% so với −42%, chủ yếu một đợt giảm 2022), cả giai đoạn thì gần như không đổi (−47,3% so với −47,7%). Cần đánh giá lại khi đã có lõi thật.
- Lưu ý: chỉ một thị trường và một lần chia mẫu, nên bằng chứng yếu.

### Bước tiếp theo
- Tầng 2 cần BCTC và cổ tức. Đang chờ người dùng chọn nguồn thay TCBS.

## 27/11/2026 – Thăm dò nguồn BCTC thay TCBS
- Run "Tai du lieu V34" #2 thất bại sau 25 phút 29 giây: do TCBS trả 403 hàng trăm lần nên chạm giới hạn thời gian. Phần giá đã commit trước đó nên không mất dữ liệu. Đã bỏ TCBS khỏi `v34/tai_du_lieu.py`.
- Thăm dò từ runner GitHub, dùng yêu cầu thường (User-Agent khai báo rõ, không giả trình duyệt, không Referer/Origin giả), có sự đồng ý của người dùng:
  - VNDirect finfo (`finfo-api.vndirect.com.vn`): hết thời gian kết nối (ConnectTimeout) cả 4 endpoint. Runner không tới được máy chủ này.
  - SSI fiin-fundamental: HTTP 403, trang "Blocked - SSI".
- Kết luận: không có nguồn BCTC công khai nào lấy được tự động từ runner GitHub. Không tiếp tục cố vượt chặn.
- Cần người dùng chọn: (a) tự cung cấp CSV BCTC và cổ tức vào `data/bctc/`, (b) cấp API key chính thức (DNSE Lightspeed hoặc SSI FastConnect) qua GitHub Secrets, (c) cho làm tạm bản chỉ dựa vào giá.

## 27/11/2026 – Nguồn BCTC thay thế: Vietcap IQ
- Thăm dò vòng 2 (yêu cầu thường, User-Agent khai báo): Vietcap IQ (`iq.vietcap.com.vn`) trả JSON HTTP 200 cho BCTC và chỉ số; CafeF, Vietstock, VPS trả 200 (HTML/JSON, chưa dùng); Simplize 404; HNX lỗi SSL.
- Tải BCTC 70 mã không lỗi: kết quả kinh doanh, cân đối kế toán, lưu chuyển tiền tệ (năm và quý, có `publicDate`), chỉ số tài chính theo quý (gồm nợ xấu, bao phủ nợ xấu cho ngân hàng), và từ điển mã chỉ tiêu. Lưu ở `data/bctc/`.
- Hạn chế: dữ liệu chỉ từ năm 2018 (8 năm báo cáo), nên bộ lọc nhiều năm dùng được từ khoảng tháng 4/2022. Chưa có lịch sử cổ tức riêng (dùng "cổ tức đã trả" trong lưu chuyển tiền tệ làm thay thế, có thể lẫn cổ tức trả cho cổ đông thiểu số). Chưa có dữ liệu cho phép thử 4 (bên liên quan), 5 (kiểm toán), 7 (người nội bộ): ghi "không đánh giá được".
