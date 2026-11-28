"""Dữ liệu và bộ lọc chất lượng cho mẫu dài (2010→nay) dựa trên BCTC năm 20 năm và lịch sử cổ tức từ CafeF.
Hiệu lực: báo cáo năm Y dùng sau cuối năm Y +90 ngày. Cổ tức: chỉ tính các sự kiện có ngày không hưởng quyền <= ngày xét."""
import glob, json, os, re
import numpy as np, pandas as pd
from tang2_chon_ma import DuLieuCoBan, NGAN_HANG, CHUA_DANH_GIA, _phep_thu_noi_bo
from du_lieu_thu_cong import DuLieuThuCong
_TC = DuLieuThuCong()


def _bang(v):
    out = {}
    for x in (v or {}).get("data", []) or []:
        try: y = int(x["year"])
        except Exception: continue
        out[y] = {"ma": {c["code"]: c["value"] for c in x.get("data", []) if c.get("value") is not None}, "kt": x.get("content") or ""}
    return out


def _bang_sec(v):
    """CDKT và LCTT của CafeF: data = danh sách phân đoạn (TN/NV, HDKD/HDDT/HDTC), mỗi phân đoạn có danh sách kỳ; gộp theo năm."""
    out = {}
    for sec in (v or {}).get("data") or []:
        for p in sec.get("data") or []:
            try: y = int(p["year"])
            except Exception: continue
            o = out.setdefault(y, {"ma": {}, "kt": p.get("content") or ""})
            for c in p.get("data") or []:
                if c.get("value") is not None: o["ma"][c["code"]] = c["value"]
    return out


def doc_co_tuc(ds):
    rows = []
    for e in ds or []:
        if e.get("type") != 1: continue
        m = re.search(r"\((-?\d+)\)", str(e.get("Time", "")))
        if not m: continue
        ngay = pd.Timestamp(int(m.group(1)), unit="ms").normalize()
        for t in e.get("Text") or []:
            tl = re.search(r"tỷ lệ\s*([\d.,:]+)\s*(%?)", t)
            if "Tiền" in t and "Cổ tức" in t: rows.append((ngay, "tien", tl.group(1) if tl else ""))
            elif "Cổ phiếu" in t and ("Cổ tức" in t or "Thưởng" in t): rows.append((ngay, "cp", tl.group(1) if tl else ""))
            elif "Thưởng" in t: rows.append((ngay, "cp", tl.group(1) if tl else ""))
    return pd.DataFrame(rows, columns=["ngay", "loai", "ty_le"])


class DuLieuDai:
    def __init__(self, thu_muc="data/cafef", co_so=None):
        self.co_so = co_so or DuLieuCoBan()       # giao dịch nội bộ, chỉ số quý
        self.nam, self.co_tuc = {}, {}
        for f in sorted(glob.glob(os.path.join(thu_muc, "[A-Z]*.json"))):
            ma = os.path.basename(f)[:-5]; d = json.load(open(f))
            kq, cd, lc = _bang(d.get("kqkd")), _bang_sec(d.get("cdkt")), _bang_sec(d.get("lctt"))
            ds = {}
            for y in kq:
                ds[y] = {"is": kq[y]["ma"], "bs": cd.get(y, {}).get("ma", {}), "cf": lc.get(y, {}).get("ma", {}), "kt": kq[y]["kt"], "hl": pd.Timestamp(y, 12, 31) + pd.Timedelta(days=90)}
            self.nam[ma] = ds; self.co_tuc[ma] = doc_co_tuc(d.get("co_tuc"))

    def __getattr__(self, ten):
        if ten in ("co_so", "nam", "co_tuc"): raise AttributeError(ten)
        return getattr(self.co_so, ten)

    def cac_nam(self, ma, ngay, n=5):
        return sorted([(y, v) for y, v in self.nam.get(ma, {}).items() if v["hl"] <= ngay])[-n:]

    def so_nam_co_tuc_tien(self, ma, ngay, n=5):
        df = self.co_tuc.get(ma)
        if df is None or df.empty: return 0
        d = df[(df.loai == "tien") & (df.ngay <= ngay) & (df.ngay > ngay - pd.Timedelta(days=365 * n))]
        return int(d.ngay.dt.year.nunique())

    def so_nam_co_tuc_bat_ky(self, ma, ngay, n=5):
        df = self.co_tuc.get(ma)
        if df is None or df.empty: return 0
        d = df[(df.ngay <= ngay) & (df.ngay > ngay - pd.Timedelta(days=365 * n))]
        return int(d.ngay.dt.year.nunique())


def _v(d, c):
    x = d.get(c); return float(x) if x is not None else np.nan


def _noi_bo(dl, ma, ngay, lnst, eps, nguong=0.005):
    bn = dl.co_so.ban_rong_noi_bo(ma, ngay)
    if bn is None or not (np.isfinite(lnst) and np.isfinite(eps) and eps > 0 and lnst > 0): return CHUA_DANH_GIA
    return bool(bn / (lnst / eps) <= nguong)   # số cổ phiếu ~ LNST mẹ / EPS


def loc_dai(dl, ma, ngay):
    """Trả về (đạt?, kq, nhân tố). Phi ngân hàng: các phép thử 1, 2, 3, 6, 7, 8 (cổ tức tiền thật), 5 (đã kiểm toán). Ngân hàng: ROE, cổ tức, nội bộ (chưa có nợ xấu trước 2018)."""
    nam = dl.cac_nam(ma, ngay, 5)
    if len(nam) < 3: return False, {"du_lieu": "thiếu lịch sử"}, None
    df = pd.DataFrame([{"y": y, "dthu": _v(v["is"], "10"), "lnst": _v(v["is"], "61") if "61" in v["is"] else _v(v["is"], "60"), "pbt": _v(v["is"], "50"),
                        "lai": abs(_v(v["is"], "24")), "khac": _v(v["is"], "40"), "eps": _v(v["is"], "70"),
                        "ocf": _v(v["cf"], "HDKD_20"), "pt": _v(v["bs"], "130"), "tk": _v(v["bs"], "140"), "ts": _v(v["bs"], "270"), "no": _v(v["bs"], "300"), "vcsh": _v(v["bs"], "400")} for y, v in nam]).set_index("y")
    n4 = df.tail(4); kq = {}
    ln = n4.lnst.sum()
    if ma in NGAN_HANG:
        roe = (n4.lnst / n4.vcsh).mean()
        kq["roe>=10%"] = bool(roe >= 0.10) if np.isfinite(roe) else CHUA_DANH_GIA
        kq["co_tuc_5nam"] = bool(dl.so_nam_co_tuc_bat_ky(ma, ngay) >= 3) if ngay >= pd.Timestamp(2018, 1, 1) else CHUA_DANH_GIA
        kq["7_noi_bo"] = _noi_bo(dl, ma, ngay, df.lnst.iloc[-1], df.eps.iloc[-1])
        nt = {"roe": roe, "ocf_ln": np.nan, "lnst": df.lnst.iloc[-1], "eps": df.eps.iloc[-1]}
        return all(v is True for v in kq.values() if v != CHUA_DANH_GIA), kq, nt
    ocf_ok = n4.ocf.notna().sum() >= 3
    kq["1_ocf_lnst"] = (bool(ln > 0 and n4.ocf.sum() / ln >= 0.8 and (n4.ocf < 0).sum() <= 1)) if ocf_ok else CHUA_DANH_GIA
    base, cur = df.iloc[-4] if len(df) >= 4 else df.iloc[0], df.iloc[-1]
    ts0, ts1 = base.pt + base.tk, cur.pt + cur.tk
    kq["2_phai_thu_ton_kho"] = bool(ts1 / ts0 - 1 <= cur.dthu / base.dthu - 1 + 0.15) if (base.dthu > 0 and ts0 > 0 and np.isfinite(ts1)) else CHUA_DANH_GIA
    ty = (n4.khac / n4.pbt).replace([np.inf, -np.inf], np.nan)
    kq["3_bat_thuong"] = bool(ty.mean() < 0.15) if ty.notna().sum() >= 2 else CHUA_DANH_GIA
    cover = (cur.pbt + cur.lai) / cur.lai if cur.lai > 0 else np.inf
    don_bay = cur.no / cur.vcsh if cur.vcsh > 0 else np.nan
    kq["6_no_vay"] = bool(cover >= 3 and don_bay <= 2.5) if np.isfinite(don_bay) else CHUA_DANH_GIA
    ktr = [dl.nam[ma][y]["kt"] for y, _ in nam[-3:]]; co = [k for k in ktr if k]
    kq["5_kiem_toan"] = bool(all(("kiểm toán" in k.lower() and "chưa" not in k.lower()) for k in co)) if co else CHUA_DANH_GIA   # trường trống = không đánh giá được
    kq["7_noi_bo"] = _noi_bo(dl, ma, ngay, df.lnst.iloc[-1], df.eps.iloc[-1])
    kq["8_co_tuc_tien_mat"] = bool(dl.so_nam_co_tuc_tien(ma, ngay) >= 4) if ngay >= pd.Timestamp(2018, 1, 1) else CHUA_DANH_GIA   # lịch sử cổ tức CafeF thưa trước 2013
    for ten, v in (("5b_y_kien_kiem_toan", _TC.kiem_toan(ma, ngay)), ("7b_cam_co", _TC.cam_co(ma, ngay))):
        if v is not None: kq[ten] = bool(v)
    roe = (n4.lnst / n4.vcsh).mean() if (n4.vcsh > 0).all() else np.nan
    nt = {"roe": roe, "ocf_ln": n4.ocf.sum() / ln if (ln > 0 and ocf_ok) else np.nan, "lnst": df.lnst.iloc[-1], "eps": df.eps.iloc[-1]}
    return all(v is True for v in kq.values() if v != CHUA_DANH_GIA), kq, nt
