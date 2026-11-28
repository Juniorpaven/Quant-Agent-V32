"""Tải BCTC năm 20 năm (KQKD; CDKT và LCTT qua tai_cafef2) và lịch sử cổ tức từ API công khai của CafeF cho mọi mã có BCTC trong data/bctc.
Yêu cầu thường, User-Agent khai báo, nghỉ giữa các lệnh; gặp 403/429 hoặc trang chặn thì dừng toàn bộ."""
import glob, json, os, sys, time
import requests
sys_path_fix = __import__('sys').path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_cafef2 as c2
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json"}
API = "https://apiweb.cafef.vn/api/v1/BCTC/GetReportDetail"
CT = "https://cafef.vn/du-lieu/Ajax/PageNew/LichSuKien.ashx?Symbol="
os.makedirs("data/cafef", exist_ok=True)
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
def bao_cao(ma, loai):
    ds, trang = [], 1
    while trang <= 3:
        j = lay(f"{API}?symbol={ma}&reportType={loai}&TypeTime=NAM&pageIndex={trang}&pageSize=20"); time.sleep(0.6)
        v = (j or {}).get("value") if isinstance(j, dict) else None
        if not v or not v.get("data"): break
        if trang == 1: tpl = v.get("templace")
        ds += v["data"]
        if len(ds) >= (v.get("count") or 0): break
        trang += 1
    return {"templace": tpl if ds else None, "data": ds}
ma_ds = [os.path.basename(f)[:-5] for f in sorted(glob.glob("data/bctc/[A-Z]*.json"))]
da_co = {os.path.basename(f)[:-5] for f in glob.glob("data/cafef/[A-Z]*.json")}
for ma in ma_ds:
    if bi_chan: break
    if ma in da_co and os.environ.get("LAM_MOI") != "1": continue
    out = {"kqkd": bao_cao(ma, "KQKD"), "cdkt": c2.bao_cao(ma, "cdkt"), "lctt": c2.bao_cao(ma, "lctt")}
    out["cdkt"]["loai_dung"] = out["lctt"]["loai_dung"] = 2
    if c2.bi_chan: break
    j = lay(CT + ma); time.sleep(0.6)
    out["co_tuc"] = (j or {}).get("Data") if isinstance(j, dict) else None
    json.dump(out, open(f"data/cafef/{ma}.json", "w"), ensure_ascii=False)
    print("cafef", ma, {k: (len(v["data"]) if isinstance(v, dict) else (len(v) if v else 0)) for k, v in out.items()}, flush=True)
