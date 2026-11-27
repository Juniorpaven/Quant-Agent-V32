"""Thăm dò vòng 3: yêu cầu thường, User-Agent khai báo, không giả danh. Nguồn nào chặn thì bỏ."""
import os, time, requests
os.makedirs("data/tham_do3", exist_ok=True)
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json, text/html"}
IQ = "https://iq.vietcap.com.vn/api/iq-insight-service"
U = {}
for ten, p in {"openapi_v3": "/v3/api-docs", "openapi_v2": "/v2/api-docs", "swagger": "/swagger-ui/index.html",
               "cty": "/v1/company/FPT", "cty_co_tuc": "/v1/company/FPT/dividend", "cty_co_tuc2": "/v1/company/FPT/dividends",
               "cty_su_kien": "/v1/company/FPT/events", "cty_co_dong": "/v1/company/FPT/shareholders",
               "cty_noi_bo": "/v1/company/FPT/insider-transaction", "cty_noi_bo2": "/v1/company/FPT/insider-transactions",
               "cty_kiem_toan": "/v1/company/FPT/auditor", "cty_ds": "/v1/company/FPT/price-history",
               "ds_ma": "/v1/company/list", "ds_ma2": "/v1/market/symbols", "bctc_nam_cu": "/v1/company/FPT/financial-statement?section=INCOME_STATEMENT&fromYear=2010"}.items():
    U["iq_" + ten] = IQ + p
for ma in ("FLC", "ROS", "HQC", "ITA", "GTN", "TTF", "HAI", "AMD", "LDG", "OGC", "SCR", "HNG"):
    t1 = int(time.time()); t0 = t1 - 86400 * 365 * 12
    U["gia_" + ma] = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={t0}&to={t1}&symbol={ma}&resolution=1D"
for ma in ("FLC", "ROS"):
    U["bctc_" + ma] = f"{IQ}/v1/company/{ma}/financial-statement?section=INCOME_STATEMENT"
U["cafef_co_tuc_ajax"] = "https://s.cafef.vn/Ajax/PageNew/DataHistory/DividendHistory.ashx?Symbol=FPT&PageIndex=1&PageSize=20"
U["vietstock_su_kien"] = "https://finance.vietstock.vn/FPT/su-kien.htm"
for ten, url in U.items():
    try:
        r = requests.get(url, headers=H, timeout=20)
        bi_chan = any(k in r.text[:3000].lower() for k in ("just a moment", "blocked", "access denied"))
        mo_ta = f"{r.status_code} {r.headers.get('content-type','')[:30]} len={len(r.text)} chan={bi_chan}"
        open(f"data/tham_do3/{ten}.txt", "w").write(mo_ta + "\n" + r.text[:6000])
    except Exception as e:
        mo_ta = f"LỖI {type(e).__name__}"
    print(ten, mo_ta, flush=True)
