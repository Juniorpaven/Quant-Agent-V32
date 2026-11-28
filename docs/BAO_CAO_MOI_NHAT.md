# Báo cáo Quant V34 – dữ liệu phiên 2026-11-27

Xem trực tuyến: https://github.com/Juniorpaven/Quant-Agent-V32/blob/main/docs/BAO_CAO_MOI_NHAT.md | Cách đọc báo cáo: https://github.com/Juniorpaven/Quant-Agent-V32/blob/main/docs/CACH_DOC_BAO_CAO.md

## Tóm tắt nhanh

- **Việc cần làm hôm nay:** **Tạm dừng mua thêm E1VFVN30** (giữ tiền mặt, không bán phần đã có).
- **Thay đổi so với lần trước:** có 1 thay đổi, xem mục 0.
- **Cần chú ý:** 4 mã chậm công bố BCTC (mục 4); độ rộng thị trường yếu (14.8% mã trên MA200); biến động bình thường.
- Danh sách mã chất lượng (mục 3) chỉ để tham khảo, không phải khuyến nghị mua.

## 0. Thay đổi so với báo cáo trước

- Mã **vào** danh sách đạt lọc chất lượng: VNM

## 1. Tầng 3: luật thị trường

- VN-Index **1653.9**, MA200 **1781.3** (-7.15%), đã dưới MA200 46 phiên liên tiếp.
- **Hướng dẫn: VN-Index dưới MA200: tạm dừng mua thêm lõi (giữ tiền mặt), không bán. Mua lại khi VN-Index vượt MA200.**

Chỉ báo tham khảo (backtest cho thấy không cải thiện lợi suất so với luật MA200, không dùng để ra quyết định):

| Chỉ báo | Giá trị | Cách hiểu |
| --- | ---: | --- |
| Độ rộng: % mã trên MA200 (122 mã thanh khoản) | 14.8% | yếu |
| Độ rộng: % mã trên MA50 | 19.7% | yếu |
| Biến động 20 phiên (năm hóa) | 19.4% (gấp 1.15 lần trung vị 1 năm) | bình thường |
| Cách đỉnh 52 tuần | -14.2% | điều chỉnh vừa |
| Giá trị giao dịch thị trường (20 phiên) | gấp 1.01 lần trung vị 1 năm | bình thường |
| Mức kéo xa MA200 | -7.2% | không kéo xa |
| Mã đang chạy nóng (tăng ≥30% trong 3 tháng hoặc ≥100% trong 12 tháng) | 0.8% (1 mã) | ít |
| Phân kỳ độ rộng (chỉ số gần đỉnh 52 tuần nhưng dưới 40% mã trên MA50) | Không | chưa |
| **Thị trường hưng phấn** (giao dịch ≥1,5 lần và cao hơn MA200 ≥10%) | Không | chưa |

Hai dòng cuối (chạy nóng, hưng phấn) là chỉ báo kiểu đảo ngược: tin tốt dồn dập, giao dịch bùng nổ và giá chạy xa thường xuất hiện khi giá đã tăng nhiều. Backtest 2010–2026 **chưa thấy giá trị dự báo**: mã chạy nóng không tăng thấp hơn đáng kể sau 3, 6, 12 tháng (chênh −0,1; 0,0; −2,4 điểm, khoảng tin cậy chứa 0); cờ hưng phấn không dự báo lợi suất thấp và luật tạm dừng mua theo cờ này không cải thiện (−0,02 đến −0,11 điểm CAGR). Chỉ để tham khảo, không dùng để ra quyết định.

## 2. Tầng 1: lõi và phân bổ

- Lõi **100% E1VFVN30** (mua đều hằng tháng). Vệ tinh đã bỏ vì backtest không cải thiện (xem mục 6).
- VN-Index dưới MA200: tạm dừng mua thêm lõi (giữ tiền mặt), không bán. Mua lại khi VN-Index vượt MA200.
- Chưa có `data/vi_the.json` nên không có bảng vị thế và tỷ lệ tiền mặt (không có dữ liệu).

## 3. Tầng 2: danh sách chất lượng (chỉ theo dõi)

Có **21/122** mã thanh khoản qua các phép thử tự động (dòng tiền kinh doanh, phải thu và tồn kho, lãi bất thường, nợ vay, cổ tức tiền thật, BCTC không quá cũ; bán ròng nội bộ chỉ là cờ cảnh báo ⚠, không loại mã; ngân hàng có bộ riêng). Backtest dài hạn (2010–2026, 866 mã gồm cả mã đã hủy niêm yết) cho thấy lõi chọn mã **ngang** chuẩn mua đều có cổ tức, chưa có ý nghĩa thống kê: đây là danh sách theo dõi, không phải khuyến nghị mua. Chưa đánh giá: ý kiến kiểm toán thật, cầm cố/ký quỹ (không có nguồn dữ liệu).

| Mã | Ngành | Điểm | ROE TB (%) | Cổ tức tiền (năm/5) | Tăng 3 tháng | Tăng 12 tháng | Đà tăng | Phép thử đạt/đánh giá được |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| MBB | Ngân hàng | 0.84 | 20.7 | 4 | -13.5% | -1.8% | bình thường | 6/6 |
| NT2 | Điện, nước & xăng dầu khí đốt | 0.81 | 14.4 | 5 | +16.0% | +2.2% | bình thường | 9/9 |
| DHC | Tài nguyên Cơ bản | 0.78 | 17.0 | 5 | -0.1% | +24.8% | bình thường | 9/9 |
| CTG | Ngân hàng | 0.67 | 21.6 | 3 | -7.4% | -11.2% | bình thường | 6/6 |
| BID | Ngân hàng | 0.6 | 18.1 | 3 | -20.5% | -15.8% | bình thường | 6/6 |
| TCB | Ngân hàng | 0.59 | 15.0 | 3 | -9.6% | -9.1% | bình thường | 6/6 |
| SHB | Ngân hàng | 0.59 | 18.2 | 2 | -15.4% | -37.5% | bình thường | 6/6 |
| ACB | Ngân hàng | 0.59 | 16.9 | 4 | -12.1% | -7.7% | bình thường | 6/6 |
| BVH | Bảo hiểm | 0.53 | 9.6 | 5 | -11.9% | +4.3% | bình thường | 8/8 |
| VNM ⚠ | Thực phẩm và đồ uống | 0.53 | 26.2 | 5 | -12.6% | -10.1% | bình thường | 8/9 |
| GAS | Điện, nước & xăng dầu khí đốt | 0.51 | 19.0 | 5 | -11.3% | +22.3% | bình thường | 9/9 |
| DPR | Hóa chất | 0.51 | 8.8 | 5 | -9.2% | -11.9% | bình thường | 9/9 |

## 4. Dữ liệu: BCTC mới và mã chậm công bố

- BCTC mới công bố trong 7 ngày: BVH (Q3/2026, công bố 2026-11-27).
- Mã chậm công bố (quá hạn quý +45 ngày hoặc năm +90 ngày, đang niêm yết): BNA (kỳ cuối Q2/2026, cần Q3/2026), CAP (kỳ cuối Q2/2026, cần Q3/2026), ECI (kỳ cuối Q3/2025, cần Q3/2026), FID (kỳ cuối Q2/2026, cần Q3/2026). Chậm nộp BCTC là một dấu hiệu cảnh báo.
- Dữ liệu BCTC cập nhật lần cuối: 2026-11-28T09:25:12.788442+00:00.
- Giá: 166 mã tải mới từ Entrade, 0 mã dùng dữ liệu đã lưu; theo dõi 164 mã đang niêm yết.

## 5. Lời bình

Tính đến ngày 27/11/2026, VN-Index đang ở mức 1653.9 điểm. Thị trường giao dịch dưới đường MA200 (1781.3 điểm), cách -7.15% và đã có 46 phiên liên tiếp duy trì trạng thái này. Độ rộng thị trường (số mã trên MA200) chỉ đạt 14.8%. VN-Index đang cách đỉnh 52 tuần -14.2%. Tỷ lệ biến động là 1.15 và tỷ lệ giao dịch đạt 1.01. Hiện tại, thị trường không có dấu hiệu hưng phấn với tỷ lệ mã chạy nóng chỉ 0.8%. Báo cáo ghi nhận 21 mã đạt lọc và 122 mã có thanh khoản. Số thay đổi so với lần trước là 1. Tỷ lệ tiền mặt: không có dữ liệu.

## 6. Tình trạng các tầng

| Tầng | Trạng thái | Kết quả backtest |
| --- | --- | --- |
| 1. Lõi | Dùng: E1VFVN30 mua đều hằng tháng | Chuẩn so sánh |
| 2. Chọn mã | Chỉ theo dõi | Ngang chuẩn có cổ tức (2010→nay: +0,52 điểm %/năm, khoảng tin cậy [−3,4; +4,7]) |
| 3. Luật thị trường | Dùng: tạm dừng mua khi dưới MA200 | CAGR ngang chuẩn, giảm MDD ở đợt giảm lớn |
| 4. Vệ tinh Wyckoff | Đã bỏ | Không cải thiện, chi phí cao hơn |

_Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư._
