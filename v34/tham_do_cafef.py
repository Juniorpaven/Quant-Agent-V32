"""Thăm dò API BCTC của CafeF (apiweb.cafef.vn) mà chính trang CafeF gọi. Yêu cầu thường, User-Agent khai báo, nghỉ giữa các lệnh; gặp chặn thì dừng."""
import json, os, time, requests
os.makedirs("data/tham_do7", exist_ok=True)
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json"}
B = "https://apiweb.cafef.vn/api/v1/BCTC/GetReportDetail"
def tom_tat(j, sau=0):
    if isinstance(j, dict): return {k: (tom_tat(v, sau + 1) if sau < 3 else type(v).__name__) for k, v in list(j.items())[:20]}
    if isinstance(j, list): return [f"list[{len(j)}]", tom_tat(j[0], sau + 1) if j and sau < 3 else None]
    return j if not isinstance(j, str) else j[:50]
cac = {}
for ten, q in {"kqkd_nam_p1_s4": "reportType=KQKD&TypeTime=NAM&pageIndex=1&pageSize=4", "kqkd_nam_p1_s20": "reportType=KQKD&TypeTime=NAM&pageIndex=1&pageSize=20",
               "kqkd_nam_p3_s4": "reportType=KQKD&TypeTime=NAM&pageIndex=3&pageSize=4", "kqkd_nam_p6_s4": "reportType=KQKD&TypeTime=NAM&pageIndex=6&pageSize=4",
               "kqkd_quy_p1_s4": "reportType=KQKD&TypeTime=QUY&pageIndex=1&pageSize=4", "kqkd_quy_p20_s4": "reportType=KQKD&TypeTime=QUY&pageIndex=20&pageSize=4",
               "cdkt_nam_p1_s4": "reportType=CDKT&TypeTime=NAM&pageIndex=1&pageSize=4", "lctt_nam_p1_s4": "reportType=LCTT&TypeTime=NAM&pageIndex=1&pageSize=4",
               "lctt_nam_p1_s4_gt": "reportType=LCGT&TypeTime=NAM&pageIndex=1&pageSize=4"}.items():
    url = f"{B}?symbol=FPT&{q}"
    try:
        r = requests.get(url, headers=H, timeout=30)
        try: j = r.json()
        except Exception: j = None
        o = {"http": r.status_code, "len": len(r.text)}
        if j is not None: o["cau_truc"] = tom_tat(j)
        open(f"data/tham_do7/{ten}.json", "w").write(r.text[:80000])
        cac[ten] = o; print(ten, json.dumps(o, ensure_ascii=False)[:300], flush=True)
        if r.status_code in (403, 429): print("dừng do bị chặn"); break
    except Exception as e: print(ten, "LỖI", type(e).__name__, flush=True)
    time.sleep(1.5)
json.dump(cac, open("data/tham_do7/_tom_tat.json", "w"), ensure_ascii=False, indent=1)
