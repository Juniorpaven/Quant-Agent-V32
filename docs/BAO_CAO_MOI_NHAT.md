# Báo cáo Quant V34 – dữ liệu phiên 2026-11-27

Xem trực tuyến: https://github.com/Juniorpaven/Quant-Agent-V32/blob/nang-cap-v34/docs/BAO_CAO_MOI_NHAT.md

## 0. Thay đổi so với báo cáo trước

Đây là báo cáo đầu tiên có theo dõi thay đổi; từ lần sau sẽ so sánh với báo cáo này.

## 1. Tầng 3: luật thị trường

- VN-Index **1653.9**, MA200 **1781.3** (-7.15%), đã dưới MA200 46 phiên liên tiếp.
- **Hướng dẫn: VN-Index dưới MA200: tạm dừng mua thêm lõi (giữ tiền mặt), không bán. Mua lại khi VN-Index vượt MA200.**

Chỉ báo tham khảo (backtest cho thấy không cải thiện lợi suất so với luật MA200, không dùng để ra quyết định):

| Chỉ báo | Giá trị |
| --- | ---: |
| Độ rộng: % mã trên MA200 (122 mã thanh khoản) | 14.8% |
| Độ rộng: % mã trên MA50 | 19.7% |
| Biến động 20 phiên (năm hóa) | 19.4% (gấp 1.15 lần trung vị 1 năm) |
| Cách đỉnh 52 tuần | -14.2% |

## 2. Tầng 1: lõi và phân bổ

- Lõi **100% E1VFVN30** (mua đều hằng tháng). Vệ tinh đã bỏ vì backtest không cải thiện (xem mục 6).
- VN-Index dưới MA200: tạm dừng mua thêm lõi (giữ tiền mặt), không bán. Mua lại khi VN-Index vượt MA200.
- Chưa có `data/vi_the.json` nên không có bảng vị thế và tỷ lệ tiền mặt (không có dữ liệu).

## 3. Tầng 2: danh sách chất lượng (chỉ theo dõi)

Có **20/122** mã thanh khoản qua các phép thử tự động (dòng tiền kinh doanh, phải thu và tồn kho, lãi bất thường, nợ vay, bán ròng nội bộ, cổ tức tiền thật, BCTC không quá cũ; ngân hàng có bộ riêng). Backtest dài hạn (2010–2026, 866 mã gồm cả mã đã hủy niêm yết) cho thấy lõi chọn mã **ngang** chuẩn mua đều có cổ tức, chưa có ý nghĩa thống kê: đây là danh sách theo dõi, không phải khuyến nghị mua. Chưa đánh giá: ý kiến kiểm toán thật, cầm cố/ký quỹ (không có nguồn dữ liệu).

| Mã | Ngành | Điểm | ROE TB (%) | Cổ tức tiền (năm/5) | Phép thử đạt/đánh giá được |
| --- | --- | ---: | ---: | ---: | ---: |
| MBB | Ngân hàng | 0.85 | 20.7 | 4 | 6/6 |
| NT2 | Điện, nước & xăng dầu khí đốt | 0.81 | 14.4 | 5 | 9/9 |
| DHC | Tài nguyên Cơ bản | 0.77 | 17.0 | 5 | 9/9 |
| CTG | Ngân hàng | 0.68 | 21.6 | 3 | 6/6 |
| BID | Ngân hàng | 0.62 | 18.1 | 3 | 6/6 |
| SHB | Ngân hàng | 0.6 | 18.2 | 2 | 6/6 |
| ACB | Ngân hàng | 0.6 | 16.9 | 4 | 6/6 |
| TCB | Ngân hàng | 0.58 | 15.0 | 3 | 6/6 |
| BVH | Bảo hiểm | 0.53 | 9.6 | 5 | 8/8 |
| DPR | Hóa chất | 0.51 | 8.8 | 6 | 9/9 |
| GAS | Điện, nước & xăng dầu khí đốt | 0.51 | 19.0 | 5 | 9/9 |
| ANV | Thực phẩm và đồ uống | 0.5 | 11.8 | 5 | 9/9 |

## 4. Dữ liệu: BCTC mới và mã chậm công bố

- BCTC mới công bố trong 7 ngày: BVH (Q3/2026, công bố 2026-11-27).
- Mã chậm công bố (quá hạn quý +45 ngày hoặc năm +90 ngày, đang niêm yết): BNA (kỳ cuối Q2/2026, cần Q3/2026), CAP (kỳ cuối Q2/2026, cần Q3/2026), ECI (kỳ cuối Q3/2025, cần Q3/2026), FID (kỳ cuối Q2/2026, cần Q3/2026). Chậm nộp BCTC là một dấu hiệu cảnh báo.
- Dữ liệu BCTC cập nhật lần cuối: 2026-11-28T09:25:12.788442+00:00.
- Giá: 166 mã tải mới từ Entrade, 0 mã dùng dữ liệu đã lưu; theo dõi 164 mã đang niêm yết.

## 5. Lời bình

Báo cáo ngày 27/11/2026 cho thấy VN-Index đạt 1653.9 điểm, nằm dưới đường MA200 (1781.3 điểm) với khoảng cách -7.15%. Đây là phiên thứ 46 liên tiếp thị trường giao dịch dưới MA200.

Độ rộng thị trường, với 14.8% số mã nằm trên MA200, cho thấy sự phân hóa. VN-Index đang cách đỉnh 52 tuần -14.2%, và tỷ lệ biến động ghi nhận là 1.15. Trong số 122 mã có thanh khoản, có 20 mã đạt bộ lọc, không thay đổi so với báo cáo trước. Tỷ lệ tiền mặt hiện không có dữ liệu.

## 6. Tình trạng các tầng

| Tầng | Trạng thái | Kết quả backtest |
| --- | --- | --- |
| 1. Lõi | Dùng: E1VFVN30 mua đều hằng tháng | Chuẩn so sánh |
| 2. Chọn mã | Chỉ theo dõi | Ngang chuẩn có cổ tức (2010→nay: +0,52 điểm %/năm, khoảng tin cậy [−3,4; +4,7]) |
| 3. Luật thị trường | Dùng: tạm dừng mua khi dưới MA200 | CAGR ngang chuẩn, giảm MDD ở đợt giảm lớn |
| 4. Vệ tinh Wyckoff | Đã bỏ | Không cải thiện, chi phí cao hơn |

_Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư._
