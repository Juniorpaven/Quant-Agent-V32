# Báo cáo đánh giá V34 (bản cuối)

Ngày lập: 28/11/2026. Nhánh `nang-cap-v34`, pull request #2. Số liệu thô nằm ở `docs/ket_qua_*.txt`, nhật ký từng lần chạy ở `docs/NHAT_KY_BACKTEST.md`, cách vận hành ở `docs/HUONG_DAN_VAN_HANH_V34.md`. Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư.

## 1. Kết luận

**Cấu trúc đề xuất triển khai:** lõi mua đều E1VFVN30 hằng tháng, kèm luật tạm dừng mua khi VN-Index dưới MA200; danh sách mã chất lượng chỉ để theo dõi. Tầng vệ tinh (Wyckoff) bỏ.

**Bằng chứng, chia theo mẫu** (CAGR/năm; chuẩn có cổ tức = VN-Index giả lập + 2,2%/năm ước lượng, vì ETF thật hơn chỉ số khoảng 2,2%/năm):

| Mẫu | Chuẩn | Tầng 2 (N=12) | Chênh lệch, khoảng tin cậy 95% | Kết luận |
| --- | --- | --- | --- | --- |
| 2021-05→nay, 188 mã chọn tay, thị trường 4,5 năm | E1VFVN30 9,88% | 5,1–9,8% tùy biến thể | khoảng tin cậy chứa 0 | Không thắng |
| 2010-05→nay, 188 mã chọn tay | 11,36% | 13,17% | +0,86 [−2,8; +4,8] | Chưa ý nghĩa; bỏ 10 mã thắng nhất thì biến mất |
| **2010-05→nay, 866 mã đầy đủ (22% đã ngừng giao dịch)** | 11,36% | 12,67% | **+0,52 [−3,4; +4,7]** | Chưa ý nghĩa; bỏ 10 mã thắng nhất vẫn 12,32% |
| **2015→nay, 866 mã đầy đủ** | 11,05% | 13,70% (có tạm dừng MA200: 14,0%) | **+1,76 [−3,7; +7,7]** | Chưa ý nghĩa |

Điều rút ra:
1. Tầng 2 **ngang chuẩn có cổ tức**, không chứng minh được lợi thế có ý nghĩa thống kê (mọi khoảng tin cậy đều chứa 0) và cũng không kém hơn. MDD và Sharpe gần như bằng nhau (ví dụ 2010→nay: −41,6% so với −42,9%; Sharpe 0,56 so với 0,57).
2. **Giá trị nằm ở bộ lọc chất lượng, không ở xếp hạng nhân tố:** chọn ngẫu nhiên trong mã đạt lọc cho 12,56% (2010→) và 13,94% (2015→), bằng xếp hạng nhân tố (12,67% và 13,70%).
3. So với rổ đều top 30 thanh khoản không lọc (gồm cả mã đã hủy niêm yết) tầng 2 thắng rất rõ (+10,9 và +13,6 điểm %/năm, có ý nghĩa), nhưng đó là chuẩn yếu: thị trường "thô" chỉ −1,1 đến +0,9%/năm. Bộ lọc chất lượng loại được phần lớn mã kém.
4. Vòng quay thấp (khoảng 9%/năm) nên trượt giá 0,3% chỉ làm mất 0,1 điểm %.
5. Không có lý do để thay lõi E1VFVN30 (đơn giản, rẻ, mua được) bằng lõi chọn mã; có thể dùng danh sách chất lượng như nguồn tham khảo hoặc nghiêng nhẹ (biến thể pha 50% cho +0,16 điểm %, không đáng kể).

Tầng 3 (VN-Index so với MA200, tạm dừng mua): CAGR ngang chuẩn, vòng quay 0%; giảm MDD rõ ở các đợt giảm lớn (walk-forward: −22,8% so với −34,5%; −28,6% so với −42,0%). Trên chuỗi VN-Index 2001–2026 (có khủng hoảng 2008), biến thể có bán 50% nâng CAGR 6,43% lên 8,59% và giảm MDD −79,9% xuống −61,4% trong 2001–2014. Giữ làm luật mặc định; hiệu quả phụ thuộc chế độ thị trường nên coi là kiểm soát rủi ro chứ không phải nguồn lợi suất.

## 2. Trạng thái từng tầng

| Tầng | Đã làm | Còn lại |
| --- | --- | --- |
| Dữ liệu | Giá điều chỉnh 2006→nay cho 872 mã (gồm 188 mã ngừng giao dịch); BCTC năm 2005–2025 (CafeF) và quý 2018→nay (Vietcap) cho 874 mã; cổ tức thật (CafeF); giao dịch nội bộ 2007→nay; cập nhật gia tăng hằng ngày, phát hiện mã mới công bố và mã chậm công bố; dữ liệu nén gọn (126 MB xuống 19 MB cho phần BCTC) | Lãi suất liên ngân hàng, ý kiến kiểm toán thật, cầm cố: không có nguồn tự động, đã dựng luồng nhập CSV (cần bạn cung cấp). Năm 2015 thiếu ở một số công ty là lỗi của nguồn (đã đồng ý giữ cách xử lý hiện tại) |
| Khung backtest | Phí, thuế, T+2,5, biên độ, lô 100, thanh khoản theo thời kỳ, trượt giá; kiểm định bootstrap theo khối; 14 kiểm thử tự động (gồm chất lượng dữ liệu, nhìn trước, nhập module); đã sửa lỗi NaN, nhìn trước và lỗi nhập module | Thuế cổ tức 5% và phí quản lý ETF chưa mô hình hóa; chuẩn VN-Index giả lập không có cổ tức (dùng thêm bản cộng 2,2%/năm) |
| Tầng 3 | MA, độ rộng, biến động, walk-forward, chuỗi 2001→nay; chỉ báo lãi suất (có kiểm thử, chờ CSV) | Lãi suất liên ngân hàng thật |
| Tầng 2 | Bộ lọc năm (mẫu dài) và TTM (quý); phép thử 1, 2, 3, 5 (đã/chưa kiểm toán; chênh lệch 4 quý), 6, 7 (bán ròng nội bộ), 8 (cổ tức tiền thật); phép thử 4 thay thế; lọc phân vị; giới hạn ngành; mẫu dài trên 866 mã; kiểm tra độ vững | Ý kiến kiểm toán thật và cầm cố (luồng CSV); nhân tố giá trị chưa dùng ở mẫu dài |
| Tầng 1 | Ghép lõi/vệ tinh hai túi vốn, độ nhạy 90/10 đến 70/30 | Mô hình đa túi vốn dùng chung tiền mặt (không cần thiết khi tầng 4 bị bỏ) |
| Tầng 4 | Wyckoff khung tuần, toàn tập mã từ 2015 (173 lệnh), 10 biến thể | Không cải thiện, quyết định bỏ |
| Tầng 6 | Báo cáo do code tạo; mail và Gemini đã kiểm thử thật trên runner; hook khởi động phiên; workflow hằng ngày có kiểm thử trước | Lịch chạy hằng ngày có hiệu lực sau khi merge (bạn đã đồng ý) |

## 3. Việc bạn có thể làm thêm
1. Merge PR #2 (xem `docs/HUONG_DAN_VAN_HANH_V34.md` mục 1).
2. Tùy chọn: nhập CSV lãi suất liên ngân hàng, ý kiến kiểm toán, cầm cố (mẫu ở `data/*.mau.csv`).
3. Cân nhắc nguồn dữ liệu chính thức có khóa API (DNSE, SSI) để thay API không chính thức, vì hai nguồn hiện dùng có thể đổi hoặc chặn bất kỳ lúc nào.
