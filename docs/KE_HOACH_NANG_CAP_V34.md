# Kế hoạch nâng cấp Quant 3D Matrix lên V34

Ngày lập: 27/11/2026. Tài liệu này là yêu cầu đầy đủ cho phiên Claude Code tiếp theo. Đọc hết trước khi viết code.

## 1. Mục tiêu

Chuyển hệ thống từ lướt sóng hằng ngày (V33) sang mô hình **lõi + vệ tinh** phục vụ tích sản dài hạn (hòn tuyết lăn), gồm 4 tầng. Mỗi tầng phải backtest đạt tiêu chí ở mục 6 rồi mới làm tầng kế tiếp. Thước đo chung: phải thắng việc mua đều hằng tháng ETF E1VFVN30 sau khi trừ toàn bộ chi phí.

## 2. Bốn tầng và thứ tự xây dựng

| Thứ tự | Tầng | Việc cần làm | Nhịp chạy |
| --- | --- | --- | --- |
| 1 | Khung backtest | Viết một lần, dùng lại cho mọi tầng (mục 5) | — |
| 2 | Tầng 3 – Luật thị trường | VN-Index so với MA200 (trên: giải ngân lõi 100%; dưới: 50%); bổ sung lãi suất liên ngân hàng qua đêm nếu có dữ liệu thật | Hằng tuần |
| 3 | Tầng 2 – Chọn mã lõi | Lọc chất lượng nhiều năm theo 8 phép thử (mục 4) + chấm điểm nhân tố chất lượng, giá trị, động lượng 6–12 tháng (bỏ tháng gần nhất); chọn 10–15 mã | Mỗi quý, sau mùa BCTC |
| 4 | Tầng 1 – Khung lõi/vệ tinh | Lõi 70–80% vốn: mua đều hằng tháng, tái đầu tư cổ tức, chỉ bán khi mã trượt lọc ở lần rà quý sau. Vệ tinh 20–30% | Hằng tháng |
| 5 | Tầng 4 – Wyckoff khung tuần | Chỉ cho mã thuộc danh sách tầng 2. Bắt buộc vùng đi ngang ≥ 6–8 tuần, Spring + Test thanh khoản thấp, hoặc SOS/LPS. Dừng lỗ theo ATR. Chỉ giữ nếu backtest chứng minh cải thiện; nếu không, gộp vốn vệ tinh vào lõi | Hằng ngày |
| 6 | Tích hợp | Nối vào luồng GitHub Actions + gửi mail. Gemini chỉ viết lời bình từ số liệu đã tính; bảng vị thế và tỷ lệ tiền mặt do code tạo | Hằng ngày |

## 3. Lỗi của V33 phải sửa hoặc loại bỏ (tham chiếu TOOL_Agent_Quant_Core_v32.py)

1. Danh sách loại trừ chỉ áp cho mã mua mới, không áp cho mã đang giữ (dòng 463, 642–666) → mail ra "Nắm giữ" và "Cảnh báo đỏ" cùng một mã.
2. Mã vừa cắt lỗ được mua lại ngay trong cùng phiên.
3. Quy tắc lệch giá ≥ 15% đặt lại giá vốn (dòng 455) che giấu khoản lỗ thật → bỏ; xử lý chia tách bằng giá điều chỉnh.
4. Đối soát theo 5 lần chạy, không theo phiên; cron chạy cả thứ Bảy, Chủ nhật → chỉ chạy ngày giao dịch, đếm theo phiên.
5. Bộ lọc OCF đọc trường `fromSale` của API TCBS, mặc định 0 nên gần như không bao giờ âm → kiểm tra lại tên trường; bỏ lọc OCF với ngân hàng.
6. Markowitz Monte Carlo 2.000 mẫu, không seed, cắt còn top 5 → thay bằng tối ưu thật (scipy) hoặc chia theo nghịch đảo biến động.
7. Prompt bắt Gemini điền số lãi suất và xu hướng 5/30 ngày từ 3 kết quả tìm kiếm web → AI tự bịa số. Bỏ yêu cầu bắt buộc; không có số thật thì ghi "không có dữ liệu".
8. Dừng lỗ cố định −5% theo giá đóng cửa, trong khi mail ghi "theo ATR" → thống nhất theo ATR.
9. Nhãn "Pha B" là mặc định, Spring không dùng để chọn mã → viết lại theo tầng 4.

## 4. Tám phép thử cho tầng 2 (người dùng đặt ra)

1. Dòng tiền kinh doanh âm nhiều quý liền trong khi báo lãi → loại. Tiêu chí gợi ý: OCF/LNST trung bình 3–5 năm ≥ 0,8.
2. Khoản phải thu và hàng tồn kho tăng nhanh hơn doanh thu.
3. Lãi từ khoản bất thường (thu nhập khác, thoái vốn, đánh giá lại, đổi cách hợp nhất, hoàn nhập dự phòng).
4. Giao dịch với bên liên quan (doanh thu, phải thu, cho vay).
5. Kiểm toán: ý kiến ngoại trừ, đổi công ty kiểm toán, chênh lệch trước/sau kiểm toán lớn.
6. Nợ vay và chi phí lãi vay tăng nhanh hơn lợi nhuận.
7. Người nội bộ bán ra, cầm cố, bị gọi ký quỹ.
8. Cổ tức tiền mặt trả đều nhiều năm (bằng chứng khó giả nhất): ưu tiên ≥ 5 năm liên tục.

Ngân hàng dùng bộ chỉ tiêu riêng: nợ xấu, nợ nhóm 2, tỷ lệ bao phủ, chi phí dự phòng so với tăng trưởng nợ xấu.
Phép thử nào không có dữ liệu tự động thì ghi rõ "không đánh giá được", không được tự gán "đạt".

## 5. Đặc tả khung backtest

- Giai đoạn: 2015 đến nay, dữ liệu ngày.
- Phí mua và bán 0,15% mỗi chiều; thuế bán 0,1%.
- Thanh toán T+2,5: cổ phiếu mua phiên T chỉ bán được từ chiều T+2.
- Biên độ HOSE ±7%: không khớp lệnh mua khi giá trần, không khớp lệnh bán khi giá sàn.
- Lô 100 cổ phiếu; chỉ giao dịch mã có giá trị giao dịch bình quân 20 phiên đủ lớn (gợi ý ≥ 10 tỷ đồng/phiên).
- Không dùng dữ liệu tương lai: BCTC quý chỉ được dùng sau hạn công bố (quý +30 ngày, báo cáo năm +90 ngày).
- Kiểm tra walk-forward: tối ưu tham số trên một đoạn, đánh giá trên đoạn sau.
- Báo cáo: CAGR, độ sụt giảm lớn nhất (MDD), Sharpe, vòng quay danh mục, tổng chi phí, so sánh với mua đều E1VFVN30 và VN-Index.

## 6. Tiêu chí đạt của mỗi tầng

- CAGR sau phí cao hơn mua đều E1VFVN30, hoặc bằng nhưng MDD thấp hơn rõ rệt.
- Kết quả giữ được ở đoạn walk-forward chưa dùng để tối ưu.
- Vòng quay danh mục phần lõi ≤ 100%/năm.
- Không tầng nào được làm kết quả chung xấu đi; nếu có, bỏ tầng đó và ghi lý do vào docs/NHAT_KY_BACKTEST.md.

## 7. Nguồn dữ liệu

- Môi trường sandbox của Claude có thể bị chặn mạng tới services.entrade.com.vn và apipubaws.tcbs.com.vn (đã kiểm tra ngày 27/11/2026: cả hai lỗi kết nối). Cách xử lý: viết workflow GitHub Actions tải dữ liệu (runner có mạng, bot hiện tại vẫn gọi được Entrade), lưu CSV vào thư mục data/ và commit; backtest chạy trên dữ liệu đã lưu.
- Giá: endpoint chart-api của Entrade (DNSE) đang dùng; khi có tài khoản nên chuyển sang nguồn chính thức: DNSE Lightspeed API, SSI FastConnect Data.
- BCTC: API TCBS (kiểm tra tên trường), đối chiếu BCTC gốc trên HOSE/HNX/Vietstock khi cần.
- Lãi suất liên ngân hàng: website Ngân hàng Nhà nước; lãi suất huy động: biểu lãi suất Big4. Lưu lịch sử để tính xu hướng thật.
- Không dùng Yahoo cho số liệu cơ bản của mã Việt Nam.

## 8. Cách làm việc

- Tự làm liên tục theo thứ tự mục 2: viết → backtest → sửa → backtest lại → sang tầng kế tiếp, cho đến khi xong cả 6 bước. Không dừng lại hỏi người dùng, trừ khi cần quyết định không thể đảo ngược.
- Làm trên nhánh `nang-cap-v34`; không sửa file V33 đang chạy và không đổi workflow run_quant.yml cho đến bước 6.
- Ghi mọi lần chạy backtest (tham số, kết quả, quyết định) vào docs/NHAT_KY_BACKTEST.md.
- Mỗi tầng xong thì commit riêng; hoàn tất thì mở pull request vào main, mô tả kết quả backtest so với E1VFVN30.
- Nội dung tiếng Việt (báo cáo, bảng, nhật ký) viết có dấu đầy đủ; chỉ tên file và tên thư mục viết không dấu.
- Đây là công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư.
