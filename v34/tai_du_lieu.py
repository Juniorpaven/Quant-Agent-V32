"""Tải dữ liệu giá (Entrade) và BCTC/cổ tức (TCBS) vào thư mục data/.
Chạy trên GitHub Actions (runner có mạng). Giá lưu CSV, BCTC lưu JSON thô."""
import json, os, sys, time
from datetime import datetime, timezone
import pandas as pd
import requests

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
HDR = {"User-Agent": "Mozilla/5.0"}
INDICES = ["VNINDEX", "VN30"]
ETF = ["E1VFVN30"]
MA_LOC = ("VCB BID CTG TCB MBB ACB VPB STB HDB TPB VIB SSI VND VCI HCM VHM VIC VRE HPG HSG NKG "
          "PVD PVS DGC DCM DPM VHC ANV PTB MWG PNJ FPT REE GAS NT2 VSH VNM SAB KBC SZC IDC VGC "
          "DIG NVL PDR DXG KDH SMC SIP DTD NTC PHR GVR BMP DHG PC1 POW PLX BVH MSN VJC GMD HAH "
          "CTD HDG VPI TCH CII LPB SHB EIB MSB OCB").split()
NGUON_BCTC = {"kqkd": "incomestatement", "cdkt": "balancesheet", "lctt": "cashflow"}


def tai_gia(ma, tu_nam=2015):
    loai = "index" if ma in INDICES else "stock"
    khung = []
    nam_nay = datetime.now().year
    for nam in range(tu_nam, nam_nay + 1):
        t0 = int(datetime(nam, 1, 1, tzinfo=timezone.utc).timestamp())
        t1 = int(datetime(nam, 12, 31, 23, 59, tzinfo=timezone.utc).timestamp())
        url = (f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{loai}"
               f"?from={t0}&to={t1}&symbol={ma}&resolution=1D")
        for lan in range(2):
            try:
                d = requests.get(url, headers=HDR, timeout=10).json()
                if d.get("c"):
                    khung.append(pd.DataFrame({
                        "Date": pd.to_datetime(d["t"], unit="s").normalize(),
                        "Open": d["o"], "High": d["h"], "Low": d["l"],
                        "Close": d["c"], "Volume": d["v"]}))
                break
            except Exception:
                time.sleep(2)
    if not khung:
        return None
    df = pd.concat(khung).drop_duplicates("Date").sort_values("Date")
    return df[(df.Close > 0) & (df.Volume >= 0)]


def tai_json(url):
    for lan in range(2):
        try:
            r = requests.get(url, headers=HDR, timeout=10)
            if r.status_code == 200:
                return r.json()
            print("  HTTP", r.status_code, url, flush=True)
        except Exception as e:
            print("  LỖI", type(e).__name__, url, flush=True)
        time.sleep(1)
    return None


def kiem_tra_ket_noi():
    t1 = int(time.time()); t0 = t1 - 86400 * 30
    for ten, url in [("Entrade", f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={t0}&to={t1}&symbol=FPT&resolution=1D"),
                     ("TCBS", "https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/FPT/cashflow?yearly=1&isAll=true")]:
        try:
            r = requests.get(url, headers=HDR, timeout=10)
            print("THỬ", ten, r.status_code, r.text[:200].replace("\n", " "), flush=True)
        except Exception as e:
            print("THỬ", ten, "LỖI", type(e).__name__, e, flush=True)


def main():
    kiem_tra_ket_noi()
    os.makedirs(f"{DATA}/gia", exist_ok=True)
    os.makedirs(f"{DATA}/bctc", exist_ok=True)
    loi = []
    for ma in INDICES + ETF + MA_LOC:
        df = tai_gia(ma)
        if df is None or len(df) < 100:
            loi.append(f"gia:{ma}")
            print("thiếu giá", ma, flush=True)
            continue
        df.to_csv(f"{DATA}/gia/{ma}.csv", index=False)
        print("gia", ma, len(df), df.Date.min().date(), df.Date.max().date(), flush=True)
    for ma in MA_LOC:
        out = {}
        for khoa, ten in NGUON_BCTC.items():
            for ky, yearly in (("quy", 0), ("nam", 1)):
                d = tai_json(f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ma}/{ten}?yearly={yearly}&isAll=true")
                out[f"{khoa}_{ky}"] = d
        out["codt"] = tai_json(f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/company/{ma}/dividend-payment-histories?page=0&size=100")
        out["ratio_nam"] = tai_json(f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ma}/financialratio?yearly=1&isAll=true")
        out["ratio_quy"] = tai_json(f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ma}/financialratio?yearly=0&isAll=true")
        if not any(out.values()):
            loi.append(f"bctc:{ma}")
            continue
        json.dump(out, open(f"{DATA}/bctc/{ma}.json", "w"), ensure_ascii=False)
        print("bctc", ma, {k: (len(v) if v else 0) for k, v in out.items()}, flush=True)
    json.dump({"cap_nhat": datetime.now(timezone.utc).isoformat(), "loi": loi},
              open(f"{DATA}/_trang_thai.json", "w"), ensure_ascii=False, indent=1)
    print("LỖI:", loi)


if __name__ == "__main__":
    main()
