"""Bổ sung đúng CDKT và LCTT (năm, 20 năm) từ API công khai của CafeF cho mọi mã đã có data/cafef/*.json. Yêu cầu thường, nghỉ giữa các lệnh; gặp chặn thì dừng."""
import glob, json, os, time, requests
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json"}
URL = {"cdkt": "https://apiweb.cafef.vn/api/v2/BCTC/GetReportCDKT", "lctt": "https://apiweb.cafef.vn/api/v1/BCTC/GetReportLCTT"}
bi_chan = False
def lay(url):
    global bi_chan
    for lan in range(2):
        try:
            r = requests.get(url, headers=H, timeout=30)
            if r.status_code in (403, 429) or "just a moment" in r.text[:500].lower(): bi_chan = True; print("BỊ CHẶN", r.status_code, url, flush=True); return None
            if r.status_code == 200: return r.json()
            print("HTTP", r.status_code, url, flush=True)
        except Exception as e: print("LỖI", type(e).__name__, url, flush=True)
        time.sleep(1)
    return None
def bao_cao(ma, khoa, loai="ALL"):
    ds, tpl, trang, meta = [], None, 1, {}
    while trang <= 3:
        j = lay(f"{URL[khoa]}?symbol={ma}&pageIndex={trang}&pageSize=20&reportType={loai}&TypeTime=NAM"); time.sleep(0.6)
        v = (j or {}).get("value") if isinstance(j, dict) else None
        if not v or not v.get("data"): break
        if trang == 1: tpl = v.get("templace"); meta = {k: v.get(k) for k in ("count", "type", "timeType")}
        ds += v["data"]
        if len(ds) >= (v.get("count") or 0): break
        trang += 1
    return {"templace": tpl, "data": ds, **meta}
if __name__ == "__main__":
    # kiểm tra cấu trúc với FPT trước
    for khoa in ("cdkt", "lctt"):
        b = bao_cao("FPT", khoa); print("FPT", khoa, "kỳ:", len(b["data"]), "template:", [t["code"] + ":" + t["name"][:25] for t in (b["templace"] or [])[:6]], "meta:", {k: b.get(k) for k in ("count", "type")}, flush=True)
        if b["data"]: print("  mã mẫu năm 2025:", [(c["code"], c["value"]) for c in b["data"][0]["data"][:5]], flush=True)
    for f in sorted(glob.glob("data/cafef/[A-Z]*.json")):
        if bi_chan: break
        ma = os.path.basename(f)[:-5]; d = json.load(open(f))
        if d.get("cdkt", {}).get("loai_dung") and d.get("lctt", {}).get("loai_dung"): continue
        d["cdkt"] = bao_cao(ma, "cdkt"); d["cdkt"]["loai_dung"] = True
        d["lctt"] = bao_cao(ma, "lctt"); d["lctt"]["loai_dung"] = True
        json.dump(d, open(f, "w"), ensure_ascii=False)
        print("cafef2", ma, len(d["cdkt"]["data"]), len(d["lctt"]["data"]), flush=True)
