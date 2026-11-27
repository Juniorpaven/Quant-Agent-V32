"""Thăm dò vòng 4: tóm tắt cấu trúc phản hồi Vietcap IQ (yêu cầu thường, User-Agent khai báo)."""
import json, os, time, requests
os.makedirs("data/tham_do4", exist_ok=True)
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json"}
IQ = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company"
def tom_tat(j, sau=0):
    if isinstance(j, dict):
        return {k: (tom_tat(v, sau + 1) if sau < 2 else type(v).__name__) for k, v in list(j.items())[:25]}
    if isinstance(j, list):
        return [f"list[{len(j)}]", tom_tat(j[0], sau + 1) if j and sau < 2 else None]
    return j if not isinstance(j, str) else j[:40]
def thu(ten, url):
    try:
        r = requests.get(url, headers=H, timeout=25)
        try: j = r.json()
        except Exception: j = None
        out = {"http": r.status_code, "len": len(r.text)}
        if j is not None: out["cau_truc"] = tom_tat(j)
        return j, out
    except Exception as e:
        return None, {"loi": type(e).__name__}
ket_qua = {}
j, o = thu("noi_bo", f"{IQ}/FPT/insider-transaction?page=0&size=2000")
if j and j.get("data"):
    c = j["data"].get("content", [])
    o["so_ban_ghi"] = len(c); o["tong"] = {k: v for k, v in j["data"].items() if k != "content"}
    o["nam_cong_bo"] = sorted({x["publicDate"][:4] for x in c if x.get("publicDate")})
    o["ma_su_kien"] = sorted({x.get("eventCode") for x in c})
    o["khoa_mau"] = sorted(c[0].keys()) if c else None
ket_qua["noi_bo"] = o
for ma in ("FPT", "ROS", "FLC", "HAI", "AMD", "GTN"):
    j, o = thu("gia", f"{IQ}/{ma}/price-history?page=0&size=5000")
    if j and j.get("data"):
        c = j["data"].get("content", [])
        o["so_ban_ghi"] = len(c); o["tong"] = {k: v for k, v in j["data"].items() if k != "content"}
        if c: o["ngay"] = [c[0].get("tradingDate"), c[-1].get("tradingDate")]; o["khoa_gia"] = sorted(k for k in c[0] if "rice" in k or "Volume" in k)[:20]
    ket_qua["gia_" + ma] = o
for p in ("dividend-history", "cash-dividend", "dividend-payment", "corporate-action", "corporate-actions", "event-calendar", "events/dividend",
          "major-shareholder", "major-shareholders", "shareholder", "ownership", "audit-opinion", "auditor-opinion", "audit", "related-party", "news", "stock-split",
          "financial-ratio", "statistics-financial?period=Y", "financial-statement?section=NOTE"):
    j, o = thu(p, f"{IQ}/FPT/{p}")
    ket_qua["thu_" + p] = o
json.dump(ket_qua, open("data/tham_do4/tom_tat.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(ket_qua, ensure_ascii=False)[:6000])
