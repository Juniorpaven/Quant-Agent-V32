"""Thăm dò lãi suất liên ngân hàng (yêu cầu thường). Chỉ ghi tóm tắt: có số liệu lãi suất qua đêm trong HTML hay không."""
import re, os, time, requests
os.makedirs("data/tham_do8", exist_ok=True)
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "text/html,application/json"}
U = ["https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/ttsk/ls", "https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/ttsk/ls/lslnh",
     "https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/ttsk/ls/ls_lnh", "https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/ttsk",
     "https://tradingeconomics.com/vietnam/interbank-rate", "https://tradingeconomics.com/vietnam/interest-rate",
     "https://vn.investing.com/rates-bonds/vietnam-overnight", "https://cafef.vn/du-lieu/lai-suat.chn", "https://s.cafef.vn/lai-suat-lien-ngan-hang.chn",
     "https://vietstock.vn/lai-suat-lien-ngan-hang.htm", "https://tcbs.com.vn/", "https://www.hnx.vn/vi-vn/trai-phieu/lai-suat-lien-ngan-hang.html"]
for i, u in enumerate(U):
    try:
        r = requests.get(u, headers=H, timeout=25)
        t = r.text; chan = any(k in t[:3000].lower() for k in ("just a moment", "captcha", "access denied", "blocked"))
        co_so = len(re.findall(r"(?:qua đêm|overnight|Qua đêm)", t)); co_ls = len(re.findall(r"\d{1,2}[.,]\d{1,2}\s*%", t))
        print(i, r.status_code, len(t), "CHẶN" if chan else "", f"nhắc 'qua đêm' {co_so} lần; số dạng %: {co_ls}", u, flush=True)
        if co_so and co_ls: open(f"data/tham_do8/{i}.html", "w").write(t[:300000])
        if r.status_code in (403, 429) or chan: continue
    except Exception as e: print(i, "LỖI", type(e).__name__, u, flush=True)
    time.sleep(1.5)
