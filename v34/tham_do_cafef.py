"""Thăm dò hẹp CafeF: các endpoint AJAX mà chính trang CafeF gọi (cổ tức, BCTC). Yêu cầu thường, User-Agent khai báo, nghỉ giữa các lệnh; gặp chặn thì dừng."""
import os, time, requests
os.makedirs("data/tham_do6", exist_ok=True)
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json, text/html"}
U = {}
for host in ("https://cafef.vn", "https://s.cafef.vn"):
    h = host.split("//")[1].split(".")[0] if host.startswith("https://s.") else "cafef"
    U[f"{h}_co_tuc"] = f"{host}/du-lieu/Ajax/PageNew/LichSuKien.ashx?Symbol=FPT"
    U[f"{h}_kqkd"] = f"{host}/du-lieu/Ajax/FinancialAjax.aspx?isBank=false&isInsurance=false&tab=ketqua&symbol=fpt"
U["cafef_kqkd_nam2015"] = "https://cafef.vn/du-lieu/Ajax/FinancialAjax.aspx?isBank=false&isInsurance=false&tab=ketqua&symbol=fpt&year=2015"
U["cafef_kqkd_trang2"] = "https://cafef.vn/du-lieu/Ajax/FinancialAjax.aspx?isBank=false&isInsurance=false&tab=ketqua&symbol=fpt&page=2"
U["cafef_candoi"] = "https://cafef.vn/du-lieu/Ajax/FinancialAjax.aspx?isBank=false&isInsurance=false&tab=candoi&symbol=fpt"
U["cafef_luuchuyen"] = "https://cafef.vn/du-lieu/Ajax/FinancialAjax.aspx?isBank=false&isInsurance=false&tab=luuchuyen&symbol=fpt"
U["cafef_chiso"] = "https://cafef.vn/du-lieu/Ajax/FinancialAjax.aspx?isBank=false&isInsurance=false&tab=chiso&symbol=fpt"
U["cafef_chiso_tt"] = "https://cafef.vn/du-lieu/Ajax/PageNew/ChiSoTaiChinh.ashx?Symbol=FPT"
for ten, url in U.items():
    try:
        r = requests.get(url, headers=H, timeout=25)
        chan = any(k in r.text[:3000].lower() for k in ("just a moment", "captcha", "access denied", "blocked"))
        open(f"data/tham_do6/{ten}.txt", "w").write(f"{r.status_code} {r.headers.get('content-type','')} len={len(r.text)}\n" + r.text[:60000])
        print(ten, r.status_code, len(r.text), "CHẶN" if chan else "", flush=True)
        if r.status_code in (403, 429) or chan: print("dừng do bị chặn"); break
    except Exception as e: print(ten, "LỖI", type(e).__name__, flush=True)
    time.sleep(1.5)
