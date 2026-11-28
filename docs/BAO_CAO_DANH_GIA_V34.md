# Báo cáo đánh giá các tầng V34

Ngày lập: 28/11/2026. Nhánh `nang-cap-v34`, pull request #2. Số liệu chi tiết từng lần chạy nằm ở `docs/NHAT_KY_BACKTEST.md`. Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư.

## 1. Kết luận ngắn và mức độ tin cậy

- Trên dữ liệu hiện có, **không tầng nào thêm vào thắng mua đều E1VFVN30 sau phí**. Tầng 3 (tạm dừng mua khi VN-Index dưới MA200) gần bằng chuẩn nhưng chưa chứng minh được lợi ích.
- Mức độ tin cậy của kết luận **thấp đến vừa**, vì các lý do sau (đã kiểm tra lại ngày 28/11/2026):
  1. **Mẫu ngắn:** tầng 2, 4 và tầng 1 chỉ chạy được từ 2021-05 (BCTC từ 2018, cần ≥3 năm), khoảng 4,5 năm, một chế độ thị trường.
  2. **Chuẩn so sánh bị một mã chi phối:** từ 2024, VIC tăng 968% và VHM 185% trong khi VIC không đạt bộ lọc tại bất kỳ mốc kiểm tra nửa năm nào (2022-05 đến 2026-11). E1VFVN30 tăng 62% so với VN-Index 46%. Phần lớn chênh lệch ở đoạn 2024–nay đến từ một mã, không nói được chất lượng thua hay thắng nói chung.
  3. **Nhiều biến thể đã thử** (hơn 25 cấu hình ở tầng 1, 2, 3, 4, chưa kể 8 lần chọn ngẫu nhiên) mà chưa có kiểm định thống kê. Kết quả "thua" nhất quán giữa các biến thể, nhưng khoảng cách với chuẩn (0,5–4 điểm % CAGR) nằm trong khả năng nhiễu của mẫu 4,5 năm.
  4. **Tập mã chọn tay** (105 mã, đã thêm 32 mã suy yếu/hủy niêm yết), chưa có lịch sử thành phần chỉ số.
- Chẩn đoán tầng 2 (2021-05→nay, chuẩn 9,88%): xếp hạng tổng hợp 6,19%; chỉ ROE 5,94%; chỉ giá trị 6,81%; chỉ động lượng 0,91%; đều tay toàn bộ mã đạt lọc (30 mã) 7,10%; chọn ngẫu nhiên trong mã đạt lọc trung bình 5,25% (dao động 2,05–8,94%). Nghĩa là bộ lọc và xếp hạng chưa thêm giá trị rõ rệt so với ngẫu nhiên trong cùng tập mã, và cả tập mã đạt lọc kém chuẩn.

## 2. Các kiểm tra lại đã làm (ngày 28/11/2026)

| Hạng mục | Kết quả |
| --- | --- |
| Lỗi trong khung backtest | Tìm thấy: 12 mã có phiên trống giá giữa kỳ làm NAV và tỷ trọng thành NaN. Đã sửa (điền giá gần nhất tối đa 10 phiên khi định giá, vẫn không khớp lệnh ngày trống). Chạy lại: số liệu không đổi, vì các mã bị ảnh hưởng không nằm trong lõi lúc đó. |
| Nhìn trước tương lai | BCTC năm dùng sau max(ngày công bố, cuối năm +90 ngày); chỉ số quý sau quý +45 ngày; giao dịch nội bộ theo ngày công bố; động lượng bỏ tháng gần nhất; lệnh khớp ở mở cửa phiên sau. Không phát hiện vi phạm trong mã. |
| Nhất quán giá | So 14 mã: giá Entrade khớp giá điều chỉnh của Vietcap IQ (tỷ số ổn định, lệch ≤ 2,6%), còn so giá thô thì lệch rất lớn. Hai nguồn nhất quán, giá đã điều chỉnh theo quyền. Chưa tách được có tái đầu tư cổ tức tiền mặt hay không. ACB có giá 0 đầu kỳ ở một nguồn nên không tính được tỷ số. |
| Mã hủy niêm yết | Giá dừng ngày cuối; vị thế đang giữ coi như mất hết sau 10 phiên không có giá (bảo thủ). Bộ lọc loại FLC, ROS, HQC, NVL trước khi sụp đổ. |
| Báo cáo trên runner | Chạy thật trên GitHub (Linux, Python 3.11, gọi Entrade thật), không gửi mail và không gọi Gemini: ra đúng số liệu. |
| Độ phủ dữ liệu | 105 mã có BCTC (89 phi ngân hàng, 16 ngân hàng); số mã đạt lọc 7 (2021-06), 19 (2022-06), 23 (2023-06), 19 (2024-06), 25 (2025-06), 27 (2026-11). Phép thử 1 loại 57/89 mã phi ngân hàng, phép thử 2 loại 53/89, nên bộ lọc rất chặt, dồn vào ngân hàng. |

## 3. Báo cáo từng tầng

### Tầng 0 – Dữ liệu

**Đã làm được**
- Giá ngày 2015→nay: 76 mã (Entrade) và 32 mã mở rộng (Vietcap IQ).
- BCTC năm, quý (có ngày công bố) và chỉ số tài chính: 105 mã, từ 2018.
- Giao dịch nội bộ 2007→nay: 105 mã (GAB và GTN thiếu).
- Workflow tải dữ liệu tự động và làm mới theo quý.

**Chưa làm được**
- TCBS bị Cloudflare chặn (403), nên bot V33 gọi TCBS thất bại âm thầm từ trước.
- BCTC trước 2018, lịch sử cổ tức riêng, ý kiến kiểm toán, giao dịch bên liên quan, cầm cố/gọi ký quỹ, lãi suất liên ngân hàng.
- Lịch sử thành phần VN30/VN-Index.

**Đề xuất**
1. BCTC trước 2018: CafeF và Vietstock trả HTML bình thường từ runner (HTTP 200); viết bộ đọc bảng BCTC, hoặc bạn xuất CSV từ Vietstock/CafeF vào `data/bctc/`, hoặc dùng API chính thức (DNSE Lightspeed, SSI FastConnect) với khóa trong GitHub Secrets. Cần kiểm tra điều khoản sử dụng trước khi thu thập hàng loạt.
2. Cổ tức: thử trang sự kiện CafeF/Vietstock (HTML), hoặc suy ra từ hệ số điều chỉnh giá của Vietcap (tách cổ tức tiền mặt với cổ phiếu thưởng bằng cách đối chiếu "cổ tức đã trả" trong lưu chuyển tiền tệ).
3. Lãi suất liên ngân hàng: trang Ngân hàng Nhà nước (kiểm tra truy cập từ runner), hoặc bạn nhập tay hằng tuần vào một CSV nhỏ.
4. Tập mã không thiên lệch: lập "vũ trụ theo thanh khoản" tại mỗi ngày (top 100 theo giá trị giao dịch 20 phiên) từ danh sách đầy đủ các mã niêm yết (cần danh sách mã từ HOSE/HNX, hoặc bạn cung cấp CSV).

### Khung backtest

**Đã làm được**
- Phí 0,15%/chiều, thuế bán 0,1%, T+2,5 (theo phiên), biên độ ±7% (không mua trần, không bán sàn), lô 100, lọc thanh khoản ≥ 10 tỷ đồng/phiên, khớp ở mở cửa phiên sau.
- Báo cáo CAGR (XIRR có dòng tiền nạp), MDD, Sharpe, vòng quay, tổng chi phí, so với mua đều E1VFVN30 và VN-Index (không phí).
- Kiểm thử bằng dữ liệu giả lập và bốn bước rà soát ở mục 2.

**Chưa làm được**
- Walk-forward đúng nghĩa (tối ưu tham số trên một đoạn rồi đánh giá đoạn sau): hiện chỉ chia hai đoạn cố định và đặt tham số trước, chưa có tối ưu.
- Kiểm định thống kê (khoảng tin cậy, hiệu chỉnh nhiều lần thử).
- Mô hình trượt giá, tác động thị trường, khớp lệnh trong phiên; T+2,5 theo buổi chiều.
- Mô phỏng ETF E1VFVN30 có phí quản lý riêng và chênh lệch giá/NAV.

**Đề xuất**
1. Bootstrap theo khối trên chênh lệch lợi suất tháng so với E1VFVN30 để có khoảng tin cậy, và tính "Sharpe đã hiệu chỉnh" theo số cấu hình đã thử.
2. Walk-forward cuốn chiếu (ví dụ tối ưu 3 năm, kiểm tra 1 năm) khi có dữ liệu BCTC dài hơn.
3. Thêm chuẩn thứ hai chống thiên lệch một mã: rổ đều trọng số các mã vốn hóa lớn trong tập, hoặc E1VFVN30 loại VIC khi có dữ liệu trọng số.
4. Thêm kịch bản trượt giá 0,1–0,3% cho mã thanh khoản thấp.

### Tầng 3 – Luật thị trường (VN-Index so với MA200)

**Đã làm được**
- Backtest 2015→nay (và hai đoạn 2015–2020, 2021→nay), 3 cửa sổ MA (150/200/250) và 2 biến thể (có bán, chỉ tạm dừng mua).
- Kết quả: biến thể có bán bị loại (CAGR đoạn kiểm tra 8,65% so với 9,72%, vòng quay ~100–118%/năm). Biến thể tạm dừng mua: CAGR 10,74% so với 10,85% cả giai đoạn, vòng quay 0%, MDD chỉ cải thiện rõ ở đoạn 2021→nay (−34% so với −42%).
- Tích hợp vào báo cáo hằng ngày.

**Chưa làm được**
- Lãi suất liên ngân hàng qua đêm (không có dữ liệu thật).
- Chưa kiểm tra trước 2015 và các chỉ báo khác (độ rộng thị trường, biến động).
- Lợi ích chưa đạt rõ ràng, nên chỉ giữ tạm.

**Đề xuất**
1. Mở rộng chuỗi VN-Index về trước 2015 để thử luật qua nhiều chế độ hơn (khủng hoảng 2008, 2011). Vietcap IQ có giá nhiều mã từ 2006 (ITA, TDH, HBC), nhưng chưa kiểm tra có chuỗi VN-Index hay không; cần thăm dò trước.
2. Thử chỉ báo thay thế: độ rộng (tỷ lệ mã trên MA50/MA200), biến động thực hiện, hoặc kết hợp hai chỉ báo; đặt tiêu chí chấp nhận trước, không chọn theo kết quả.
3. Lãi suất liên ngân hàng: nhập tay vào CSV hoặc thu thập từ trang Ngân hàng Nhà nước, rồi thử làm điều kiện phụ (lãi suất tăng nhanh thì giữ thêm tiền mặt).

### Tầng 2 – Chọn mã lõi

**Đã làm được**
- Bộ lọc nhiều năm: phép thử 1 (OCF/LNST), 2 (phải thu và tồn kho so với doanh thu), 3 (lãi bất thường), 6 (nợ vay, khả năng trả lãi), 7 một phần (bán ròng của người nội bộ trong 12 tháng), 8 thay thế (cổ tức đã trả trong lưu chuyển tiền tệ ≥ 4/5 năm), quy tắc BCTC không quá 15 tháng; bộ riêng cho ngân hàng (nợ xấu, bao phủ, tăng tín dụng, ROE).
- Chấm điểm nhân tố: chất lượng, giá trị, động lượng 6–12 tháng bỏ tháng gần nhất; rà ngày 15 của tháng 2, 5, 8, 11; chỉ bán khi mã trượt lọc.
- Kết quả: mọi biến thể thấp hơn chuẩn (tốt nhất 9,38% so với 9,88%). Chẩn đoán ở mục 1.

**Chưa làm được**
- Phép thử 4 (giao dịch bên liên quan), 5 (kiểm toán), 7 phần cầm cố/gọi ký quỹ: không có dữ liệu tự động; đang ghi "không đánh giá được".
- Cổ tức thật (hiện dùng khoản "đã trả" làm thay thế, có thể lẫn cổ tức trả cho cổ đông thiểu số).
- BCTC quý để tính số 4 quý gần nhất (hiện dùng dữ liệu năm, có độ trễ tới 15 tháng).
- Độ nhạy ngưỡng: các ngưỡng đặt trước theo gợi ý kế hoạch; phép thử 1 và 2 loại hơn một nửa số mã phi ngân hàng, nên lõi dồn vào ngân hàng.

**Đề xuất**
1. Phép thử 4 thay thế bằng chỉ báo từ cân đối kế toán đã có: (phải thu nội bộ + cho vay ngắn/dài hạn + phải thu khác)/tổng tài sản và tốc độ tăng của nó.
2. Phép thử 5 thay thế: chênh lệch giữa tổng LNST bốn quý (chưa kiểm toán) và LNST năm (đã kiểm toán) khi cả hai có trong dữ liệu; kiểm tra trước xem dữ liệu quý có bị điều chỉnh lại sau kiểm toán không.
3. Hiệu chỉnh ngưỡng theo phân vị (ví dụ OCF/LNST trong nhóm 60% tốt nhất) và giới hạn mỗi ngành tối đa 3–4 mã; đặt quy tắc trước rồi chạy một lần, không chọn theo CAGR.
4. Dùng lõi lai: E1VFVN30 làm lõi chính, nghiêng 20–30% sang mã đạt lọc (biến thể pha 50% cho 8,36–9,38%, gần chuẩn nhất), thay vì lõi chọn mã toàn phần.
5. Dùng BCTC quý (TTM) để cập nhật bộ lọc hằng quý thay vì chờ báo cáo năm.

### Tầng 1 – Khung lõi/vệ tinh

**Đã làm được**
- Quy tắc lõi nằm trong tầng 2: nạp đều hằng tháng, chỉ mua thêm, chỉ bán khi mã trượt lọc ở lần rà quý sau.
- Bản ghép xấp xỉ bằng hai túi vốn độc lập (chia nạp 75%/25%), 2021-05→nay: lõi tầng 2 + vệ tinh Wyckoff 7,05%; lõi E1VFVN30 + vệ tinh Wyckoff 9,60%; lõi tầng 2 + E1VFVN30 7,37%; chuẩn 9,88%.
- Giá đã điều chỉnh theo quyền nên cổ tức được phản ánh trong giá (một phần).

**Chưa làm được**
- Mô hình hai túi vốn có cân bằng lại, bán từ vệ tinh sang lõi.
- Tái đầu tư cổ tức tiền mặt mô hình riêng (không có dòng cổ tức riêng).
- Chưa quyết định tỷ lệ lõi/vệ tinh bằng dữ liệu, mới thử 75/25.

**Đề xuất**
1. Cho khung chạy đa túi vốn trong một tài khoản dùng chung tiền mặt, với quy tắc cân bằng lại thưa (hằng quý) và bán vệ tinh chốt lãi sang lõi.
2. Thử tỷ lệ 90/10 và 80/20 như phân tích độ nhạy sau khi có chuẩn thống kê (mục khung backtest).
3. Khi có lịch sử cổ tức tiền mặt, mô hình hóa tái đầu tư để tách khỏi hiệu chỉnh giá.

### Tầng 4 – Wyckoff khung tuần (vệ tinh)

**Đã làm được**
- Tín hiệu tuần: vùng đi ngang ≥ 8 tuần (biên độ ≤ 30%), Spring + Test khối lượng thấp, SOS (vượt đỉnh vùng, khối lượng ≥ 1,5 lần); dừng lỗ 2 ATR, bám 3 ATR; tối đa 5 mã, mỗi mã 5% NAV; chỉ mã đạt lọc hoặc mọi mã.
- Kết quả 2021-05→nay: mã đạt lọc 9,75%, mọi mã 9,91%, so với 9,88% của chuẩn; vòng quay 79% và 154%/năm. Nằm trong biên nhiễu, không ổn định giữa hai đoạn.

**Chưa làm được**
- Phân tích độ nhạy tham số (độ dài vùng, biên độ, ngưỡng khối lượng, hệ số ATR).
- Định nghĩa Spring/Test dùng dữ liệu ngày tổng hợp thành tuần, chưa có dữ liệu trong phiên.
- Chưa có số lệnh đủ lớn để thống kê (51 lệnh có lọc, 89 lệnh không lọc trong 4,5 năm).

**Đề xuất**
1. Mở rộng mẫu bằng cách chạy tín hiệu trên toàn bộ 105 mã từ 2015 (tín hiệu chỉ cần giá, không cần BCTC) để có hàng trăm lệnh, rồi đánh giá riêng "có bộ lọc chất lượng" cho giai đoạn từ 2021.
2. Thử hai biến thể đơn giản hơn làm đối chứng: chỉ SOS, chỉ Spring + Test.
3. Nếu sau đó vẫn không cải thiện, giữ kết luận gộp vốn vệ tinh vào lõi (đúng mục 2 kế hoạch).

### Tầng 6 – Tích hợp

**Đã làm được**
- `v34/bao_cao_v34.py`: bảng do code tạo (luật thị trường, vị thế và tiền mặt, danh sách chất lượng); Gemini chỉ viết lời bình từ số liệu đã tính; chỉ gửi vào ngày có phiên.
- Workflow `run_quant_v34.yml` (thứ Hai–thứ Sáu), V33 chỉ còn chạy tay; làm mới dữ liệu theo quý.
- Kiểm thử trên runner không gửi mail: đúng số liệu.
- Người nhận mail lấy từ secret `EMAIL_NHAN`, không để địa chỉ trong mã.

**Chưa làm được**
- Gửi mail thật và gọi Gemini thật chưa kiểm tra (cần khóa trong GitHub Secrets).
- Workflow lịch chưa chạy thật vì chỉ có hiệu lực sau khi merge vào `main`.
- Chưa có `data/vi_the.json`, nên chưa có bảng vị thế.
- Các lỗi V33 mục 1, 2, 3, 6, 8, 9 chỉ "hết" vì V33 không còn chạy theo lịch; mã V33 chưa được sửa.

**Đề xuất**
1. Sau khi merge: chạy tay `run_quant_v34.yml` một lần để kiểm tra mail và Gemini, rồi mới bật lịch.
2. Bạn tạo `data/vi_the.json` (số lượng E1VFVN30 và tiền mặt) và đặt secret `EMAIL_NHAN`.
3. Nếu muốn giữ khả năng chọn lọc cổ phiếu ngắn hạn, viết lại phần V33 thành module riêng với các sửa lỗi ở mục 3 kế hoạch, và chỉ bật sau khi qua backtest.

## 4. Thứ tự việc nên làm tiếp (đề xuất)

1. Kiểm định thống kê và chuẩn thứ hai (rẻ, cho biết kết luận có đáng tin không).
2. Chạy tín hiệu tầng 4 trên toàn bộ tập mã từ 2015 (rẻ, chỉ cần giá).
3. Phép thử 4 và 5 thay thế từ dữ liệu đã có, rồi hiệu chỉnh ngưỡng theo phân vị.
4. Mở rộng BCTC trước 2018 (cần quyết định của bạn về nguồn: CSV tự cung cấp, parse CafeF/Vietstock, hoặc API chính thức).
5. Merge và kiểm thử mail/Gemini thật.
