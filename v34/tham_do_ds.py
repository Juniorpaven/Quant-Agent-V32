"""Thăm dò: (1) danh sách mã niêm yết đầy đủ; (2) dữ liệu quý CafeF để dựng năm thiếu 2015; (3) nguồn lãi suất liên ngân hàng khác. Yêu cầu thường, User-Agent khai báo; gặp chặn thì bỏ nguồn đó."""
import json, os, re, time, requests
os.makedirs("data/tham_do9", exist_ok=True)
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json, text/html"}
def lay(ten, url, luu=True):
    try:
        r = requests.get(url, headers=H, timeout=30); t = r.text
        chan = any(k in t[:3000].lower() for k in ("just a moment", "captcha", "access denied", "blocked"))
        print(ten, r.status_code, len(t), "CHẶN" if chan else "", url[:110], flush=True)
        if luu and r.status_code == 200 and not chan: open(f"data/tham_do9/{ten}.txt", "w").write(t[:400000])
        return r if (r.status_code == 200 and not chan) else None
    except Exception as e: print(ten, "LỖI", type(e).__name__, url[:100], flush=True)
    time.sleep(1.2)
for ten, u in {"vci_getall": "https://trading.vietcap.com.vn/api/price/symbols/getAll", "vci_getall2": "https://mt.vietcap.com.vn/api/price/symbols/getAll",
               "cafef_suggest_a": "https://s.cafef.vn/Ajax/AutoSuggestSymbol.ashx?query=A", "cafef_suggest_vn": "https://s.cafef.vn/Ajax/AutoSuggestSymbol.ashx?query=VN",
               "iq_search": "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/search?keyword=FP", "iq_listing": "https://iq.vietcap.com.vn/api/iq-insight-service/v1/market/listing",
               "hnx_root": "https://hnx.vn/", "hnx_ls": "https://hnx.vn/vi-vn/thi-truong-tp/lai-suat-lien-ngan-hang.html"}.items():
    lay(ten, u); time.sleep(1.2)
# dữ liệu quý CafeF cho HPG (thiếu năm 2015 trong dữ liệu năm)
for ten, loai in (("cafef_quy_kqkd", "KQKD"),):
    for trang in (1, 2, 3, 4, 5, 6):
        r = lay(f"{ten}_p{trang}", f"https://apiweb.cafef.vn/api/v1/BCTC/GetReportDetail?symbol=HPG&reportType={loai}&TypeTime=QUY&pageIndex={trang}&pageSize=20"); time.sleep(1.2)
        if r:
            v = (r.json() or {}).get("value") or {}; print("   kỳ:", [(x.get("year"), x.get("quater"), x.get("type")) for x in v.get("data", [])][:40], "count", v.get("count"), flush=True)
r = lay("cafef_quy_cdkt_p1", "https://apiweb.cafef.vn/api/v2/BCTC/GetReportCDKT?symbol=HPG&pageIndex=1&pageSize=20&reportType=ALL&TypeTime=QUY"); time.sleep(1.2)
if r:
    v = (r.json() or {}).get("value") or {}; sec = (v.get("data") or [{}])[0]; print("   CDKT quý kỳ:", [(x.get("year"), x.get("quater")) for x in sec.get("data", [])][:40], flush=True)
r = lay("cafef_luyke_lctt", "https://apiweb.cafef.vn/api/v1/BCTC/GetReportLCTT?symbol=HPG&pageIndex=1&pageSize=20&reportType=ALL&TypeTime=LUYKE"); time.sleep(1.2)
if r:
    v = (r.json() or {}).get("value") or {}; sec = (v.get("data") or [{}])[0]; print("   LCTT lũy kế kỳ:", [(x.get("year"), x.get("quater"), x.get("time")) for x in sec.get("data", [])][:40], flush=True)
