"""Tải mở rộng từ Vietcap IQ (yêu cầu thường): (1) giá điều chỉnh + BCTC của mã hủy niêm yết/suy yếu để giảm thiên lệch người sống sót;
(2) giao dịch nội bộ cho mọi mã (phép thử 7)."""
import json, os, sys, time
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_du_lieu as td
from tien_ich import ghi_bctc_manh, ghi_noibo

MA_THEM = ("FLC ROS HAI AMD GTN ITA HQC TTF LDG OGC SCR HNG GAB KLF ART FIT TGG DLG HBC TNT SJF ASM TDH HDC "
           "CEO LCG ITC DRH FIR EVG VIX BCG GEX").split()
DATA = td.DATA
IQ = td.IQ + "/company"


def trang(url, size=1000):
    """Đọc mọi trang của endpoint dạng content/page của Vietcap IQ."""
    out, p = [], 0
    while True:
        d = td.tai_iq(f"{url}{'&' if '?' in url else '?'}page={p}&size={size}")
        time.sleep(0.3)
        if not d or not d.get("content"): break
        out += d["content"]
        if d.get("last") or p >= 30: break
        p += 1
    return out


def tai_gia_iq(ma):
    ds = trang(f"{IQ}/{ma}/price-history")
    if not ds: return None
    df = pd.DataFrame(ds)
    lay = lambda a, b: df[a] if a in df else df[b]
    out = pd.DataFrame({"Date": pd.to_datetime(df["tradingDate"]).dt.normalize(),
                        "Open": lay("openPriceAdjusted", "openPrice") / 1000, "High": lay("highestPriceAdjusted", "highestPrice") / 1000,
                        "Low": lay("lowestPriceAdjusted", "lowestPrice") / 1000, "Close": lay("closePriceAdjusted", "closePrice") / 1000,
                        "Volume": df["totalMatchVolume"]})
    out = out[(out.Close > 0) & (out.Volume >= 0)].drop_duplicates("Date").sort_values("Date")
    return out if len(out) > 100 else None


def tai_noi_bo(ma):
    ds = trang(f"{IQ}/{ma}/insider-transaction", size=2000)
    khoa = ["publicDate", "startDate", "endDate", "eventCode", "actionTypeCode", "actionTypeEn", "actionTypeVi", "shareBeforeTrade",
            "shareAfterTrade", "shareRegister", "shareAcquire", "tradeStatusEn", "tradeStatusVi", "roleNameVi", "traderNameVi", "relativeNameVi"]
    return [{k: x.get(k) for k in khoa} for x in ds]


def main():
    os.makedirs(f"{DATA}/gia", exist_ok=True); os.makedirs(f"{DATA}/bctc", exist_ok=True); os.makedirs(f"{DATA}/noibo", exist_ok=True)
    loi = {"gia": [], "bctc": [], "noibo": []}
    for ma in MA_THEM:
        df = tai_gia_iq(ma)
        if df is None: loi["gia"].append(ma); print("thiếu giá", ma, flush=True)
        else:
            df.to_csv(f"{DATA}/gia/{ma}.csv", index=False); print("gia", ma, len(df), df.Date.min().date(), df.Date.max().date(), flush=True)
        out = {}
        for khoa, sec in (("kqkd", "INCOME_STATEMENT"), ("cdkt", "BALANCE_SHEET"), ("lctt", "CASH_FLOW")):
            out[khoa] = td.tai_iq(f"{td.IQ}/company/{ma}/financial-statement?section={sec}"); time.sleep(0.3)
        out["chi_so"] = td.tai_iq(f"{td.IQ}/company/{ma}/statistics-financial"); time.sleep(0.3)
        if out["kqkd"]: ghi_bctc_manh(f"{DATA}/bctc/{ma}.json", out); print("bctc", ma, flush=True)
        else: loi["bctc"].append(ma)
    for ma in td.MA_LOC + MA_THEM:
        ev = tai_noi_bo(ma)
        if ev: ghi_noibo(f"{DATA}/noibo/{ma}.json", ev); print("noibo", ma, len(ev), flush=True)
        else: loi["noibo"].append(ma)
    json.dump({"cap_nhat": pd.Timestamp.utcnow().isoformat(), "loi": loi}, open(f"{DATA}/_trang_thai_mo_rong.json", "w"), ensure_ascii=False, indent=1)
    print("LỖI", loi)


if __name__ == "__main__":
    main()
