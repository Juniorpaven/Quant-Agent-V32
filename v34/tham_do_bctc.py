"""Thăm dò vòng 2: nguồn BCTC công khai khác, yêu cầu thường, User-Agent khai báo rõ, không giả danh."""
import os, requests
os.makedirs("data/tham_do2", exist_ok=True)
H = {"User-Agent": "quant-agent-v34-research/1.0", "Accept": "application/json, text/html"}
UNG_VIEN = {
 "vietcap_iq_kqkd": "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/FPT/financial-statement?section=INCOME_STATEMENT",
 "vietcap_iq_chiso": "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/FPT/statistics-financial",
 "simplize_bctc": "https://api2.simplize.vn/api/company/fi/income-statement/FPT?period=Q&size=20",
 "simplize_co_tuc": "https://api2.simplize.vn/api/company/dividend/FPT",
 "cafef_kqkd": "https://s.cafef.vn/bao-cao-tai-chinh/FPT/IncSta/2024/0/0/0/ket-qua-hoat-dong-kinh-doanh-cong-ty-co-phan-fpt.chn",
 "cafef_co_tuc": "https://s.cafef.vn/hose/FPT-cong-ty-co-phan-fpt.chn",
 "vietstock_tai_chinh": "https://finance.vietstock.vn/FPT/tai-chinh.htm",
 "vps_ho_so": "https://bgapidatafeed.vps.com.vn/getliststockdata/FPT",
 "hnx_cong_bo": "https://www.hnx.vn/",
 "hsx_cong_bo": "https://www.hsx.vn/",
}
for ten, url in UNG_VIEN.items():
    try:
        r = requests.get(url, headers=H, timeout=15)
        bi_chan = any(k in r.text[:3000].lower() for k in ("just a moment", "blocked", "access denied"))
        mo_ta = f"{r.status_code} {r.headers.get('content-type','')} len={len(r.text)} chan={bi_chan}"
        open(f"data/tham_do2/{ten}.txt", "w").write(mo_ta + "\n" + r.text[:4000])
    except Exception as e:
        mo_ta = f"LỖI {type(e).__name__}"
    print(ten, mo_ta, flush=True)
