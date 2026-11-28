"""Lấy kỳ quý mới nhất từ CafeF (nguồn thứ hai) cho mọi mã để kiểm chéo độ mới và giá trị với Vietcap IQ. Yêu cầu thường, nghỉ giữa các lệnh; gặp chặn thì dừng."""
import glob, json, os, time, requests
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json"}
API = "https://apiweb.cafef.vn/api/v1/BCTC/GetReportDetail"
os.makedirs("data/cafef_quy", exist_ok=True)
for f in sorted(glob.glob("data/bctc/[A-Z]*.json")):
    ma = os.path.basename(f)[:-5]
    try:
        r = requests.get(f"{API}?symbol={ma}&reportType=KQKD&TypeTime=QUY&pageIndex=1&pageSize=4", headers=H, timeout=30)
        if r.status_code in (403, 429): print("BỊ CHẶN", r.status_code); break
        v = (r.json() or {}).get("value") or {}
        ds = [{"nam": x.get("year"), "quy": x.get("quater"), "thoi_gian": x.get("time"), "noi_dung": x.get("content"), "loai": x.get("type"),
               "ln_sau_thue": next((c["value"] for c in x.get("data", []) if c["code"] == "60"), None), "ln_me": next((c["value"] for c in x.get("data", []) if c["code"] == "61"), None),
               "doanh_thu": next((c["value"] for c in x.get("data", []) if c["code"] == "10"), None)} for x in (v.get("data") or [])]
        json.dump(ds, open(f"data/cafef_quy/{ma}.json", "w"), ensure_ascii=False); print(ma, [(d["nam"], d["quy"], d["noi_dung"]) for d in ds][:2], flush=True)
    except Exception as e: print(ma, "LỖI", type(e).__name__, flush=True)
    time.sleep(0.6)
