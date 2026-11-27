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
                     ("VNDirect", "https://finfo-api.vndirect.com.vn/v4/ratios/latest?filter=code:FPT")]:
        try:
            r = requests.get(url, headers=HDR, timeout=10)
            print("THỬ", ten, r.status_code, r.text[:200].replace("\n", " "), flush=True)
        except Exception as e:
            print("THỬ", ten, "LỖI", type(e).__name__, e, flush=True)


IQ = "https://iq.vietcap.com.vn/api/iq-insight-service/v1"
HDR_IQ = {"User-Agent": "quant-agent-v34-research/1.0", "Accept": "application/json"}


def tai_iq(url):
    for lan in range(2):
        try:
            r = requests.get(url, headers=HDR_IQ, timeout=20)
            if r.status_code == 200:
                return r.json().get("data")
            print("  HTTP", r.status_code, url, flush=True)
            if r.status_code in (403, 429):
                return None
        except Exception as e:
            print("  LỖI", type(e).__name__, url, flush=True)
        time.sleep(1)
    return None


def tai_bctc():
    os.makedirs(f"{DATA}/bctc", exist_ok=True)
    # từ điển mã chỉ tiêu (nếu có) để ánh xạ isa1, bsa1, cfa1...
    for ten, url in [("tu_dien_1", f"{IQ}/company/FPT/financial-statement/metrics"),
                     ("tu_dien_2", f"{IQ}/financial-statement/metrics"),
                     ("tu_dien_3", f"{IQ}/company/FPT/financial-statement?section=CASH_FLOW&metrics=true")]:
        try:
            r = requests.get(url, headers=HDR_IQ, timeout=20)
            print("tu_dien", ten, r.status_code, len(r.text), flush=True)
            if r.status_code == 200:
                open(f"{DATA}/bctc/_{ten}.json", "w").write(r.text[:300000])
        except Exception as e:
            print("tu_dien", ten, "LỖI", type(e).__name__, flush=True)
    loi = []
    for ma in MA_LOC:
        out = {}
        for khoa, sec in (("kqkd", "INCOME_STATEMENT"), ("cdkt", "BALANCE_SHEET"), ("lctt", "CASH_FLOW")):
            out[khoa] = tai_iq(f"{IQ}/company/{ma}/financial-statement?section={sec}")
            time.sleep(0.3)
        out["chi_so"] = tai_iq(f"{IQ}/company/{ma}/statistics-financial")
        time.sleep(0.3)
        if not out["kqkd"]:
            loi.append(ma); print("thiếu BCTC", ma, flush=True); continue
        json.dump(out, open(f"{DATA}/bctc/{ma}.json", "w"), ensure_ascii=False)
        print("bctc", ma, {k: (list(v.keys()) if isinstance(v, dict) else (len(v) if v else 0)) for k, v in out.items()}, flush=True)
    json.dump({"cap_nhat": datetime.now(timezone.utc).isoformat(), "loi_bctc": loi},
              open(f"{DATA}/_trang_thai_bctc.json", "w"), ensure_ascii=False, indent=1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "bctc":
        return tai_bctc()
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
    # BCTC: TCBS bị Cloudflare chặn (403) nên tạm bỏ; chờ nguồn thay thế (xem docs/NHAT_KY_BACKTEST.md)
    json.dump({"cap_nhat": datetime.now(timezone.utc).isoformat(), "loi": loi},
              open(f"{DATA}/_trang_thai.json", "w"), ensure_ascii=False, indent=1)
    print("LỖI:", loi)


if __name__ == "__main__":
    main()
