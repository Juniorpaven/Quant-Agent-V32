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

## 27/11/2026 – Tầng 2: chọn mã lõi (lọc chất lượng + nhân tố)
Cấu hình (đặt trước khi chạy, không dò tham số): lọc theo thời điểm (BCTC năm +90 ngày, chỉ số quý +45 ngày). Phi ngân hàng: (1) OCF/LNST 4 năm ≥ 0,8 và không quá 1 năm OCF âm; (2) phải thu + tồn kho 3 năm không tăng quá doanh thu 15 điểm %; (3) thu nhập khác ròng/LNTT < 15%; (6) khả năng trả lãi ≥ 3 và nợ vay/VCSH ≤ 1,5; (8) cổ tức tiền mặt đã trả ≥ 4/5 năm. Ngân hàng: nợ xấu ≤ 3%, bao phủ ≥ 70%, tăng tín dụng ≤ 30%, ROE bình quân ≥ 10%. Phép thử 4, 5, 7: "không đánh giá được". Điểm nhân tố: xếp hạng trung bình chất lượng (ROE, OCF/LN), giá trị (LN/vốn hóa), động lượng 6–12 tháng bỏ tháng gần nhất. Rà vào ngày 15 của tháng 2, 5, 8, 11; chỉ bán khi mã trượt lọc; nạp hằng tháng chỉ mua thêm; khe chưa lấp mua E1VFVN30. Dữ liệu BCTC chỉ từ 2018 nên chạy từ 2021-05.
Kiểm tra giá: không có khoảng trống kiểu chia cổ phiếu chưa điều chỉnh (biến động lớn nhất khớp biên độ HNX/UPCOM), coi như giá đã điều chỉnh.

| Giai đoạn | Chiến lược | CAGR | MDD | Vòng quay/năm |
| --- | --- | --- | --- | --- |
| 2021-05 → nay | Mua đều E1VFVN30 | 9,88% | −42,28% | 0% |
| 2021-05 → nay | T2 N=12 | 5,06% | −41,38% | 28,5% |
| 2021-05 → nay | T2 N=12 + tạm dừng MA200 | 4,52% | −33,13% | 26,4% |
| 2021-05 → nay | T2 N=12, trần 4 ngân hàng | 5,74% | −41,87% | 20,1% |
| 2021-05 → nay | T2 N=15 | 6,17% | −40,44% | 26,6% |
| 2021-05 → nay | T2 N=12, pha 50% E1VFVN30 | 7,65% | −40,35% | 14,7% |
| 2021-05 → nay | T2 N=12, trần 4 NH + pha 50% | 8,29% | −41,29% | 11,5% |
| 2021-05 → 2023 | Mua đều E1VFVN30 / T2 N=12 | −6,74% / +6,20% | −42,28% / −41,38% | — |
| 2024 → nay | Mua đều E1VFVN30 / T2 N=12 | +11,04% / −0,86% | −15,84% / −20,42% | — |

Nhận xét: lõi thắng ở 2021–2023 (giai đoạn giảm), thua nặng từ 2024 vì tập mã đạt lọc dồn vào ngân hàng (8/12 mã) và bỏ lỡ nhóm kéo VN-Index (VN-Index 2024→nay +46%, lõi chọn mã không giữ Vingroup). Không biến thể nào thắng mua đều.
**Quyết định: loại tầng 2 làm lõi** (không đạt tiêu chí mục 6: CAGR thấp hơn chuẩn). Lõi dùng E1VFVN30. Danh sách mã đạt lọc giữ lại để theo dõi, không phải khuyến nghị mua. Hạn chế: chỉ ~4,5 năm dữ liệu, tập mã là danh sách hiện tại (thiên lệch người sống sót, càng làm kết quả tầng 2 đáng ngờ chứ không bất lợi hơn cho nó), một chế độ thị trường.

## 27/11/2026 – Tầng 4: Wyckoff khung tuần (vệ tinh)
Cấu hình: vùng đi ngang ≥ 8 tuần (biên độ ≤ 30%); vào khi Spring + Test khối lượng thấp (< 0,7 lần TB 10 tuần) hoặc SOS (đóng cửa vượt đỉnh vùng, khối lượng ≥ 1,5 lần); dừng lỗ 2 ATR14 và bám 3 ATR; tối đa 5 mã, mỗi mã 5% NAV (vệ tinh tối đa 25%), vốn chưa dùng nằm trong E1VFVN30; chỉ mã đạt lọc tầng 2.

| Giai đoạn | Chiến lược | CAGR | MDD | Vòng quay/năm | Lệnh vào |
| --- | --- | --- | --- | --- | --- |
| 2021-05 → nay | Mua đều E1VFVN30 | 9,88% | −42,28% | 0% | — |
| 2021-05 → nay | Vệ tinh Wyckoff (mã đạt lọc) | 9,72% | −42,47% | 86,4% | 51 |
| 2021-05 → nay | Vệ tinh Wyckoff (mọi mã) | 9,86% | −41,18% | 151,3% | 89 |
| 2021-05 → 2023 | Chuẩn / có lọc / không lọc | −6,74% / −6,87% / −7,34% | — | — | — |
| 2024 → nay | Chuẩn / có lọc / không lọc | 11,04% / 11,32% / 11,81% | — | — | — |

**Quyết định: bỏ tầng 4, gộp vốn vệ tinh vào lõi** (đúng quy định mục 2: không chứng minh được cải thiện). Chênh lệch trong biên nhiễu, vòng quay cao, không ổn định giữa hai đoạn.

## 27/11/2026 – Tầng 1 và kết quả cuối
- Cấu trúc cuối: lõi 100% mua đều E1VFVN30 hằng tháng + luật tạm dừng khi VN-Index dưới MA200 (tầng 3, giữ tạm, chưa đạt rõ ràng). Không có vệ tinh. Danh sách chất lượng chỉ để theo dõi.
- So với chuẩn: tầng 3 "tạm dừng" 2015–nay CAGR 10,74% so với 10,85%, vòng quay 0%.
- **Kết quả trung thực: hệ thống V34 không thắng mua đều E1VFVN30 sau phí.** Mua đều E1VFVN30 là chuẩn mà mọi tầng thêm vào đều không vượt qua.

## 27/11/2026 – Tầng 6: tích hợp
- Thêm `v34/bao_cao_v34.py`: bảng luật thị trường, vị thế và tỷ lệ tiền mặt (đọc `data/vi_the.json` do người dùng khai) và danh sách chất lượng đều do code tạo. Gemini chỉ viết lời bình từ số liệu đã tính, không tìm kiếm web; không có số thì ghi "không có dữ liệu". Chỉ gửi mail khi có phiên giao dịch (sửa lỗi 4: chạy cả cuối tuần/ngày lễ).
- Workflow mới `run_quant_v34.yml` (thứ Hai–thứ Sáu, 16:00); `run_quant.yml` chỉ còn chạy tay (V33 bị tắt lịch). `tai_du_lieu_v34.yml` làm mới BCTC vào ngày 20 của tháng 2, 5, 8, 11.
- Người nhận mail lấy từ secret `EMAIL_NHAN` (mặc định gửi cho `EMAIL_USER`); không còn địa chỉ trong mã. Cần đặt secret `EMAIL_NHAN` nếu muốn gửi nhiều người.
- Chưa kiểm tra gửi mail thật và gọi Gemini thật trong sandbox (chỉ chạy khô được).
- Các lỗi V33 mục 3: 1, 2, 3, 6, 8, 9 không còn vì V33 không còn chạy theo lịch (không còn vị thế đa phiên hay dừng lỗ −5%); 4 đã sửa; 5 xác nhận là 403 TCBS; 7 đã bỏ yêu cầu AI điền số. Chưa sửa mã V33 cũ (giữ nguyên để tham chiếu).

## 27/11/2026 – Mở rộng dữ liệu để xử lý hạn chế, chạy lại tầng 2 và tầng 4
Nguồn mới (Vietcap IQ, yêu cầu thường, User-Agent khai báo): giá điều chỉnh và BCTC của 32 mã suy yếu hoặc hủy niêm yết (FLC, ROS, HAI, AMD, HQC, ITA, TTF, LDG, OGC, SCR, HNG…; GTN không có dữ liệu), và giao dịch nội bộ 2007–2026 cho 104/105 mã (GAB không có). Tập mã nay là 105 mã. Giá mã hủy niêm yết dừng ở ngày cuối, vị thế đang giữ coi như mất hết giá trị (bảo thủ).
Thay đổi bộ lọc (đặt trước khi chạy lại): thêm phép thử 7 (bán ròng đã thực hiện của người nội bộ trong 12 tháng > 0,5% số cổ phiếu lưu hành thì loại; chỉ xét mua/bán, không có cầm cố, gọi ký quỹ) và quy tắc BCTC mới nhất không quá 15 tháng (ngân hàng: chỉ số quý không quá 200 ngày) để mã ngừng công bố không lọt qua bằng số liệu cũ. Bộ lọc loại đúng FLC, ROS, HQC, NVL tại các thời điểm 2021–2023.
Vẫn không có nguồn tự động: phép thử 4 (bên liên quan), 5 (kiểm toán), lịch sử cổ tức riêng, BCTC trước 2018 (đã thử nhiều tên endpoint, đều 404).

### Tầng 2 chạy lại (2021-05 → nay, chuẩn E1VFVN30: CAGR 9,88%, MDD −42,28%)
| Biến thể | CAGR | MDD | Vòng quay/năm | 2021–2023 | 2024–nay |
| --- | --- | --- | --- | --- | --- |
| T2 N=12 | 6,19% | −43,01% | 33,1% | +7,34% | −1,97% |
| T2 N=12 + tạm dừng MA200 | 5,03% | −33,34% | 30,9% | +5,09% | −1,88% |
| T2 N=12, trần 4 ngân hàng | 7,37% | −41,41% | 24,7% | +3,10% | +0,71% |
| T2 N=15 | 5,64% | −40,64% | 30,8% | +6,49% | −1,92% |
| T2 N=12, pha 50% E1VFVN30 | 8,36% | −41,13% | 17,5% | +1,65% | +3,26% |
| T2 N=12, trần 4 NH + pha 50% | 9,38% | −40,01% | 14,8% | +0,05% | +5,25% |
(Chuẩn: 2021–2023 −6,74%, 2024–nay +11,04%.) **Quyết định không đổi: loại tầng 2 làm lõi** (biến thể tốt nhất vẫn thấp hơn chuẩn 0,5 điểm %, MDD tốt hơn chỉ 2,3 điểm %, không "rõ rệt"; đoạn 2024–nay thua nặng).

### Tầng 4 chạy lại
| Chiến lược | CAGR 2021-05→nay | MDD | Vòng quay/năm | 2021–2023 | 2024–nay |
| --- | --- | --- | --- | --- | --- |
| Mua đều E1VFVN30 | 9,88% | −42,28% | 0% | −6,74% | +11,04% |
| Vệ tinh Wyckoff (mã đạt lọc) | 9,75% | −42,56% | 79,0% | −6,81% | +11,57% |
| Vệ tinh Wyckoff (mọi mã) | 9,91% | −41,18% | 154,0% | −7,61% | +12,00% |
**Quyết định không đổi: bỏ tầng 4, gộp vốn vệ tinh vào lõi** (chênh lệch trong biên nhiễu, không ổn định giữa hai đoạn).

### Kết luận sau mở rộng dữ liệu
Giảm thiên lệch người sống sót và thêm phép thử 7 không đổi kết luận: không tầng nào thêm vào thắng mua đều E1VFVN30 sau phí. Hạn chế còn lại: chỉ ~4,5 năm dữ liệu BCTC, một chế độ thị trường, thiếu phép thử 4 và 5, cổ tức dùng thay thế từ lưu chuyển tiền tệ, danh sách mã vẫn do chọn tay (chưa có lịch sử thành phần chỉ số).

## 28/11/2026 – Rà soát lại các tầng
Chi tiết ở `docs/BAO_CAO_DANH_GIA_V34.md`. Tóm tắt:
- Sửa khung: giá phiên trống khi định giá (12 mã). Chạy lại tầng 2: số liệu không đổi.
- Kiểm tra nhất quán giá (14 mã): Entrade khớp giá điều chỉnh của Vietcap IQ (lệch ≤ 2,6%). Đính chính ghi chú trước: giá đã điều chỉnh theo quyền, không phải "chưa điều chỉnh"; chưa tách được cổ tức tiền mặt.
- Chuẩn E1VFVN30 từ 2024 bị VIC chi phối (VIC +968%, VHM +185%, không đạt lọc ở mốc nào), nên kết luận "tầng 2 thua" ở đoạn 2024–nay kém chắc chắn hơn đã nêu.
- Chẩn đoán tầng 2 (2021-05→nay, chuẩn 9,88%): điểm tổng hợp 6,19%; chỉ ROE 5,94%; chỉ giá trị 6,81%; chỉ động lượng 0,91%; đều tay mọi mã đạt lọc (N=30) 7,10%; ngẫu nhiên trong mã đạt lọc 5,25% trung bình (2,05–8,94%, 8 lần).
- Tầng 1 ghép (hai túi vốn độc lập, nạp 75%/25%, 2021-05→nay): lõi T2 + Wyckoff 7,05%; lõi E1VFVN30 + Wyckoff 9,60%; lõi T2 + E1VFVN30 7,37%. Quyết định không đổi.
- Kiểm thử báo cáo V34 trên runner (mạng thật, không gửi mail, không Gemini): đúng.
- Độ phủ: 105 mã có BCTC; số mã đạt lọc 7 → 27 từ 2021-06 đến 2026-11; phép thử 1 loại 57/89 và phép thử 2 loại 53/89 mã phi ngân hàng (2024-06).
