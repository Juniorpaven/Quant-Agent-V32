"""Tải hàng loạt cho toàn bộ cổ phiếu HSX, HNX và đã hủy niêm yết (danh sách data/ds_ma.json), nén gọn.
Dùng: python tai_ds_lon.py <lát> <tổng số lát>. Yêu cầu thường, User-Agent khai báo, nghỉ giữa các lệnh; gặp 403/429 thì dừng.
Mỗi mã: giá điều chỉnh (Vietcap IQ) -> data/gia_dai/<mã>.csv.gz; BCTC (Vietcap IQ) -> data/bctc; giao dịch nội bộ -> data/noibo; BCTC năm và cổ tức (CafeF) -> data/cafef."""
import glob, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_du_lieu as td, tai_mo_rong as mr, tai_cafef2 as c2
from tien_ich import ghi_bctc_manh, ghi_noibo, ghi_cafef, ghi_gia_gz
CT = "https://cafef.vn/du-lieu/Ajax/PageNew/LichSuKien.ashx?Symbol="
API1 = "https://apiweb.cafef.vn/api/v1/BCTC/GetReportDetail"


def kqkd_cafef(ma):
    ds, trang = [], 1
    while trang <= 3:
        j = c2.lay(f"{API1}?symbol={ma}&reportType=KQKD&TypeTime=NAM&pageIndex={trang}&pageSize=20"); time.sleep(0.5)
        v = (j or {}).get("value") if isinstance(j, dict) else None
        if not v or not v.get("data"): break
        ds += v["data"]
        if len(ds) >= (v.get("count") or 0): break
        trang += 1
    return {"data": ds}


def co(ma, thu_muc, duoi): return os.path.exists(f"{thu_muc}/{ma}{duoi}")


def main(lat, tong):
    ds = json.load(open("data/ds_ma.json"))
    ma_ds = sorted({x["ma"] for x in ds if x["loai"] == "STOCK" and x["san"] in ("HSX", "HNX", "DELISTED") and x["ma"] and x["ma"].isalpha() and len(x["ma"]) == 3})
    ma_ds = [m for i, m in enumerate(ma_ds) if i % tong == lat]
    print(f"lát {lat}/{tong}: {len(ma_ds)} mã", flush=True)
    os.makedirs("data/gia_dai", exist_ok=True); os.makedirs("data/ds_lon_log", exist_ok=True)
    kq = {"gia": [], "bctc": [], "noibo": [], "cafef": []}
    for k, ma in enumerate(ma_ds):
        if c2.bi_chan: print("dừng do bị chặn", flush=True); break
        if not (co(ma, "data/gia_dai", ".csv") or co(ma, "data/gia_dai", ".csv.gz")):
            df = mr.tai_gia_iq(ma)
            if df is None: kq["gia"].append(ma)
            else: ghi_gia_gz(f"data/gia_dai/{ma}.csv.gz", df)
        if not co(ma, "data/bctc", ".json"):
            out = {}
            for khoa, sec in (("kqkd", "INCOME_STATEMENT"), ("cdkt", "BALANCE_SHEET"), ("lctt", "CASH_FLOW")): out[khoa] = td.tai_iq(f"{td.IQ}/company/{ma}/financial-statement?section={sec}"); time.sleep(0.3)
            out["chi_so"] = td.tai_iq(f"{td.IQ}/company/{ma}/statistics-financial"); time.sleep(0.3)
            if out["kqkd"] and out["cdkt"] and out["lctt"]: ghi_bctc_manh(f"data/bctc/{ma}.json", out)
            else: kq["bctc"].append(ma)
        if not co(ma, "data/noibo", ".json"):
            ev = mr.tai_noi_bo(ma)
            if ev: ghi_noibo(f"data/noibo/{ma}.json", ev)
            else: kq["noibo"].append(ma)
        if not co(ma, "data/cafef", ".json"):
            out = {"kqkd": kqkd_cafef(ma), "cdkt": c2.bao_cao(ma, "cdkt"), "lctt": c2.bao_cao(ma, "lctt")}
            j = c2.lay(CT + ma); time.sleep(0.5); out["co_tuc"] = (j or {}).get("Data") if isinstance(j, dict) else None
            if out["kqkd"]["data"]: ghi_cafef(f"data/cafef/{ma}.json", out)
            else: kq["cafef"].append(ma)
        if k % 10 == 0: print(f"  {k+1}/{len(ma_ds)} {ma}", flush=True)
    json.dump(kq, open(f"data/ds_lon_log/lat{lat}.json", "w"), ensure_ascii=False)
    print("thiếu:", {k: len(v) for k, v in kq.items()}, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
