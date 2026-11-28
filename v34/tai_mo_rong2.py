"""Đợt tải 3 (yêu cầu thường, User-Agent khai báo, nghỉ giữa các lệnh; gặp 403/429/captcha thì bỏ nguồn đó):
(1) mở rộng tập mã (giá, BCTC, giao dịch nội bộ) từ Vietcap IQ; (2) VN-Index trước 2015 từ Entrade;
(3) thăm dò lãi suất liên ngân hàng và CafeF (BCTC cũ, cổ tức)."""
import json, os, sys, time
import pandas as pd, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_du_lieu as td, tai_mo_rong as mr

THEM2 = ("AAA BCM BSR BWE CMG CRE CSV CTR CTS DBC DGW DHC DPR DXS EVF FCN FRT FTS HAG HHV HT1 HUT IJC IMP KDC KOS LHG NAB NLG NTL PAN PPC PVT "
         "QCG SBT SCS SHS SJS SSB TCM TDM TLG TNH VCG VCS VDS VOS VPG VSC VTP YEG BAF DRC HVN PGV PET SGT HVG TCR VIS TNG PGD GEG ELC HID "
         "CTI DAH VPH SCI SAM DQC VNS NBB CCL AGR APG BSI CTF EIB KSB DDV TIP JVC FUCVREIT").split()
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json, text/html"}
os.makedirs("data/tham_do5", exist_ok=True)


def mo_rong():
    ok = {"gia": [], "bctc": [], "noibo": []}; loi = {"gia": [], "bctc": [], "noibo": []}
    co_san = {os.path.basename(f)[:-4] for f in os.listdir(f"{td.DATA}/gia")}
    for ma in THEM2:
        if ma in co_san: continue
        df = mr.tai_gia_iq(ma)
        if df is None: loi["gia"].append(ma); print("thiếu giá", ma, flush=True); continue
        df.to_csv(f"{td.DATA}/gia/{ma}.csv", index=False); ok["gia"].append(ma)
        out = {}
        for khoa, sec in (("kqkd", "INCOME_STATEMENT"), ("cdkt", "BALANCE_SHEET"), ("lctt", "CASH_FLOW")):
            out[khoa] = td.tai_iq(f"{td.IQ}/company/{ma}/financial-statement?section={sec}"); time.sleep(0.3)
        out["chi_so"] = td.tai_iq(f"{td.IQ}/company/{ma}/statistics-financial"); time.sleep(0.3)
        if out["kqkd"]: json.dump(out, open(f"{td.DATA}/bctc/{ma}.json", "w"), ensure_ascii=False); ok["bctc"].append(ma)
        else: loi["bctc"].append(ma)
        ev = mr.tai_noi_bo(ma)
        if ev: json.dump(ev, open(f"{td.DATA}/noibo/{ma}.json", "w"), ensure_ascii=False); ok["noibo"].append(ma)
        else: loi["noibo"].append(ma)
        print("ok", ma, len(df), flush=True)
    json.dump({"ok": ok, "loi": loi}, open(f"{td.DATA}/_trang_thai_mo_rong2.json", "w"), ensure_ascii=False, indent=1)


def vnindex_cu():
    for ma, loai in (("VNINDEX", "index"), ("VN30", "index"), ("HNX", "index")):
        khung = []
        for nam in range(2000, 2015):
            t0 = int(pd.Timestamp(nam, 1, 1).timestamp()); t1 = int(pd.Timestamp(nam, 12, 31).timestamp())
            try:
                d = requests.get(f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{loai}?from={t0}&to={t1}&symbol={ma}&resolution=1D", headers=H, timeout=15).json()
                if d.get("c"): khung.append(pd.DataFrame({"Date": pd.to_datetime(d["t"], unit="s").normalize(), "Open": d["o"], "High": d["h"], "Low": d["l"], "Close": d["c"], "Volume": d["v"]}))
            except Exception as e: print("lỗi", ma, nam, type(e).__name__, flush=True)
            time.sleep(0.3)
        if khung:
            df = pd.concat(khung).drop_duplicates("Date").sort_values("Date"); df.to_csv(f"data/tham_do5/{ma}_truoc_2015.csv", index=False)
            print("cu", ma, len(df), df.Date.min().date(), df.Date.max().date(), flush=True)
        else: print("cu", ma, "không có", flush=True)


def tham_do():
    U = {"sbv_ls": "https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/ttsk/ls",
         "cafef_ls_lnh": "https://cafef.vn/du-lieu/lai-suat-lien-ngan-hang.chn", "vietstock_ls": "https://finance.vietstock.vn/lai-suat-lien-ngan-hang",
         "cafef_kqkd_2012": "https://s.cafef.vn/bao-cao-tai-chinh/FPT/IncSta/2012/0/0/0/ket-qua-hoat-dong-kinh-doanh-cong-ty-co-phan-fpt.chn",
         "cafef_kqkd_2024": "https://s.cafef.vn/bao-cao-tai-chinh/FPT/IncSta/2024/0/0/0/ket-qua-hoat-dong-kinh-doanh-cong-ty-co-phan-fpt.chn",
         "cafef_cdkt_2024": "https://s.cafef.vn/bao-cao-tai-chinh/FPT/BSheet/2024/0/0/0/bang-can-doi-ke-toan-cong-ty-co-phan-fpt.chn",
         "cafef_lctt_2024": "https://s.cafef.vn/bao-cao-tai-chinh/FPT/CashFlow/2024/0/0/0/luu-chuyen-tien-te-gian-tiep-cong-ty-co-phan-fpt.chn",
         "cafef_co_tuc": "https://s.cafef.vn/hose/FPT-cong-ty-co-phan-fpt.chn", "cafef_su_kien": "https://s.cafef.vn/Ajax/Events_RelatedNew.aspx?symbol=FPT&floorID=0&configID=0&PageIndex=1&PageSize=30&Type=3"}
    for ten, url in U.items():
        try:
            r = requests.get(url, headers=H, timeout=25)
            chan = any(k in r.text[:3000].lower() for k in ("just a moment", "captcha", "access denied", "blocked"))
            open(f"data/tham_do5/{ten}.html", "w").write(r.text[:600000])
            print(ten, r.status_code, len(r.text), "chặn" if chan else "", flush=True)
        except Exception as e: print(ten, "LỖI", type(e).__name__, flush=True)
        time.sleep(1)


if __name__ == "__main__":
    for f in (vnindex_cu, tham_do, mo_rong): f()
