"""Thăm dò nguồn cho lãi suất liên ngân hàng, kiểm toán, cầm cố/ký quỹ. Yêu cầu thường, User-Agent khai báo; gặp chặn thì bỏ nguồn đó."""
import os, re, time, requests
os.makedirs("data/tham_do10", exist_ok=True)
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "text/html,application/json,text/csv"}
def lay(ten, url, luu=True):
    try:
        r = requests.get(url, headers=H, timeout=30); t = r.text
        chan = any(k in t[:3000].lower() for k in ("just a moment", "captcha", "access denied", "blocked"))
        print(ten, r.status_code, len(t), "CHẶN" if chan else "", url[:100], flush=True)
        if luu and r.status_code == 200 and not chan: open(f"data/tham_do10/{ten}.txt", "w").write(t[:300000])
        return t if (r.status_code == 200 and not chan) else None
    except Exception as e: print(ten, "LỖI", type(e).__name__, url[:90], flush=True)
    finally: time.sleep(1.2)
for ten, u in {"fred_ib3m": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IR3TIB01VNM156N", "fred_dis": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INTDSRVNM193N",
               "fred_ib_vn2": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01VNM156N", "fred_lend": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INTGSTVNM193N"}.items(): lay(ten, u)
t = lay("te_ib", "https://tradingeconomics.com/vietnam/interbank-rate", luu=False)
if t:
    for m in re.finditer(r"(?:interbank rate|Interbank Rate)[^<]{0,260}", t): print("  TE:", re.sub(r"\s+", " ", m.group(0))[:300]); break
    print("  TE meta:", re.findall(r'<meta name="description" content="([^"]{0,300})', t)[:1], flush=True)
t = lay("cafef_kyquy", "https://cafef.vn/du-lieu/GiaoDichKyQuy.aspx?symbol=FPT")
if t: print("  ký quỹ: số <tr>:", t.count("<tr"), "| từ khóa:", {k: t.count(k) for k in ("ký quỹ", "cầm cố", "Cầm cố", "margin", "Ký quỹ")}, flush=True)
lay("cafef_kyquy2", "https://cafef.vn/du-lieu/Ajax/PageNew/GiaoDichKyQuy.ashx?Symbol=FPT")
lay("iq_events", "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/FPT/events?page=0&size=50")
lay("iq_news", "https://iq.vietcap.com.vn/api/iq-insight-service/v1/news?ticker=FPT&page=0&size=20")
