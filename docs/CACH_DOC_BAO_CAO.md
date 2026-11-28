# Cách đọc báo cáo Quant V34

Báo cáo gửi mail mỗi ngày có phiên giao dịch (16:00) và cũng xem được trực tuyến ở `docs/BAO_CAO_MOI_NHAT.md`. Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư.

## Đọc nhanh trong 30 giây
1. Mở phần **Tóm tắt nhanh** ở đầu báo cáo. Đây là phần duy nhất cần để hành động.
2. **Việc cần làm hôm nay** chỉ có hai khả năng:
   - *Mua đều E1VFVN30 như bình thường*: nếu đến phiên đầu tháng thì mua phần tiền đều đặn của tháng.
   - *Tạm dừng mua thêm E1VFVN30*: không mua thêm, **không bán** phần đã có, giữ tiền mặt; hệ thống tự báo khi đến lúc mua lại.
3. Nếu **Thay đổi so với lần trước** là "không có" thì không cần đọc thêm.

Hệ thống chỉ đưa ra một quyết định duy nhất: mua đều hay tạm dừng mua E1VFVN30. Mọi mục còn lại là thông tin tham khảo.

## Từng mục trong báo cáo
**Mục 0. Thay đổi so với báo cáo trước.** Báo khi: tín hiệu MA200 đổi chiều (đây là thay đổi quan trọng nhất, cần hành động), có mã vào hoặc rời danh sách chất lượng, có mã mới chậm công bố BCTC, hoặc có BCTC mới công bố.

**Mục 1. Tầng 3, luật thị trường.**
- **MA200:** trung bình giá đóng cửa 200 phiên gần nhất của VN-Index. VN-Index **dưới** MA200 nghĩa là thị trường đang trong xu hướng giảm dài hạn, hệ thống tạm dừng mua; **trên** MA200 thì mua bình thường. Báo cáo cũng cho biết đã ở phía hiện tại bao nhiêu phiên liên tiếp (số phiên càng ít càng dễ đổi chiều).
- Bảng **chỉ báo tham khảo** (độ rộng, biến động, cách đỉnh) cho bức tranh thị trường nhưng **không dùng để ra quyết định**, vì backtest cho thấy chúng không cải thiện lợi suất:
  - *Độ rộng*: tỷ lệ cổ phiếu thanh khoản đang nằm trên đường trung bình của chính nó. Dưới 30% là yếu (phần lớn cổ phiếu đang giảm), 30–60% trung bình, trên 60% mạnh.
  - *Biến động*: mức dao động của VN-Index so với trung vị một năm. Dưới 1,3 lần là bình thường, 1,3–2 lần là cao, trên 2 lần là rất cao.
  - *Cách đỉnh 52 tuần*: VN-Index đang thấp hơn đỉnh một năm bao nhiêu phần trăm.

**Mục 2. Tầng 1, lõi và phân bổ.** Lõi là 100% E1VFVN30 (quỹ ETF theo VN30), mua đều hằng tháng. Nếu bạn khai `data/vi_the.json` thì có bảng vị thế và tỷ lệ tiền mặt; không thì mục này không có số liệu.

**Mục 3. Tầng 2, danh sách chất lượng (chỉ theo dõi).** Các mã qua một loạt phép thử tự động về chất lượng doanh nghiệp.
- *Điểm*: xếp hạng trung bình về chất lượng và đà tăng giá, từ 0 đến 1; không phải xác suất lãi.
- *ROE TB*: lợi nhuận trên vốn chủ sở hữu bình quân các năm gần đây.
- *Cổ tức tiền (năm/5)*: trong 5 năm gần nhất có mấy năm chia cổ tức bằng tiền.
- *Phép thử đạt/đánh giá được*: ví dụ 6/6 là đạt cả 6 phép thử có dữ liệu. Con số thứ hai nhỏ hơn tổng số phép thử vì một số phép thử thiếu dữ liệu và được ghi "không đánh giá được".
- **Đừng mua một mã chỉ vì nó có trong danh sách.** Backtest dài hạn cho thấy lõi chọn mã chỉ ngang với mua đều E1VFVN30, chưa có ý nghĩa thống kê. Danh sách để bạn tìm hiểu thêm; hệ thống không đánh giá ý kiến kiểm toán thật và cầm cố cổ phiếu, nên cần tự kiểm tra hai điều này trước khi cân nhắc bất kỳ mã nào.

**Mục 4. Dữ liệu.** BCTC mới công bố trong 7 ngày, và các mã **chậm công bố** (quý quá hạn 45 ngày, năm quá hạn 90 ngày). Chậm nộp BCTC thường là dấu hiệu cảnh báo về quản trị; cẩn trọng với các mã này.

**Mục 5. Lời bình.** Do Gemini viết, chỉ diễn đạt lại các con số đã tính, không thêm tin tức hay số liệu nào.

**Mục 6. Tình trạng các tầng.** Tầng nào đang dùng, tầng nào chỉ theo dõi, tầng nào đã bỏ, kèm kết quả backtest.

## Ví dụ: đọc báo cáo phiên 27/11/2026
- VN-Index 1.653,9, thấp hơn MA200 (1.781,3) 7,15% và đã dưới MA200 46 phiên liên tiếp, nên việc cần làm là **tạm dừng mua thêm E1VFVN30**.
- Độ rộng 14,8% (yếu): hầu hết cổ phiếu cũng đang dưới đường trung bình của chúng, nhất quán với tín hiệu dưới MA200. Biến động bình thường (1,15 lần); cách đỉnh 52 tuần −14,2% (điều chỉnh vừa).
- Vì không có tín hiệu đổi chiều, phần "thay đổi" là không có; có 4 mã chậm công bố BCTC cần cẩn trọng nếu quan tâm đến các mã đó.

## Từ điển ngắn
| Thuật ngữ | Nghĩa |
| --- | --- |
| E1VFVN30 | Quỹ ETF mô phỏng chỉ số VN30, mua bán như cổ phiếu |
| MA200 | Trung bình 200 phiên của giá đóng cửa |
| Tạm dừng mua | Không mua thêm, không bán phần đã có |
| TTM | Số liệu bốn quý gần nhất cộng lại |
| MDD | Mức sụt giảm lớn nhất từ đỉnh đến đáy |
| CAGR | Lợi suất bình quân mỗi năm |
| Độ rộng | Tỷ lệ cổ phiếu mạnh trên toàn thị trường |

## Giới hạn cần nhớ
- Hệ thống không đánh giá lãi suất liên ngân hàng, ý kiến kiểm toán thật và cầm cố/ký quỹ (không có nguồn dữ liệu tự động đáng tin).
- Kết quả backtest là quá khứ, không đảm bảo tương lai; luật MA200 giúp giảm mức sụt giảm ở các đợt giảm lớn nhưng không ngăn được sụt giảm.
