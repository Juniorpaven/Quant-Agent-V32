"""Tầng 2: lọc chất lượng nhiều năm (các phép thử mục 4 kế hoạch) + chấm điểm nhân tố, chọn mã lõi.
Dữ liệu theo thời điểm: chỉ dùng báo cáo đã công bố (năm +90 ngày, quý +45 ngày; lấy ngày muộn hơn giữa ngày công bố thật và quy tắc)."""
import json, glob, os
import numpy as np, pandas as pd

NGAN_HANG = {"VCB", "BID", "CTG", "TCB", "MBB", "ACB", "VPB", "STB", "HDB", "TPB", "VIB", "LPB", "SHB", "EIB", "MSB", "OCB"}
CHUA_DANH_GIA = "không đánh giá được"


def _hieu_luc(ky_nam, cong_bo, tre_ngay):
    het_ky = pd.Timestamp(ky_nam, 12, 31)
    quy_tac = het_ky + pd.Timedelta(days=tre_ngay)
    cb = pd.to_datetime(cong_bo) if cong_bo else quy_tac
    return max(cb, quy_tac)


class DuLieuCoBan:
    def __init__(self, thu_muc="data/bctc"):
        self.nam, self.chi_so = {}, {}
        for f in sorted(glob.glob(os.path.join(thu_muc, "[A-Z]*.json"))):
            ma = os.path.basename(f)[:-5]
            d = json.load(open(f))
            if not d.get("kqkd"): continue
            nam = {}
            for khoa in ("kqkd", "cdkt", "lctt"):
                for r in (d.get(khoa) or {}).get("years", []) or []:
                    y = r["yearReport"]
                    nam.setdefault(y, {"hieu_luc": _hieu_luc(y, r.get("publicDate"), 90)})
                    nam[y].setdefault(khoa, r)
                    nam[y]["hieu_luc"] = max(nam[y]["hieu_luc"], _hieu_luc(y, r.get("publicDate"), 90))
            self.nam[ma] = nam
            cs = []
            for r in d.get("chi_so") or []:
                if r.get("quarter") in (1, 2, 3, 4):
                    kt = pd.Timestamp(int(r["year"]), int(r["quarter"]) * 3, 1) + pd.offsets.MonthEnd(0)
                    cs.append((kt + pd.Timedelta(days=45), r))
            self.chi_so[ma] = sorted(cs, key=lambda x: x[0])
        self.noibo = {}
        for f in sorted(glob.glob(os.path.join(os.path.dirname(thu_muc), "noibo", "*.json"))):
            ma = os.path.basename(f)[:-5]
            ev = []
            for x in json.load(open(f)):
                if x.get("tradeStatusEn") != "Done" or x.get("actionTypeEn") not in ("Buy", "Sell") or not x.get("publicDate"): continue
                acq = x.get("shareAcquire") or 0.0
                if x["actionTypeEn"] == "Sell":
                    sl = -acq if acq < 0 else max((x.get("shareBeforeTrade") or 0) - (x.get("shareAfterTrade") or 0), 0)
                    ev.append((pd.Timestamp(x["publicDate"]), float(sl)))
                else:
                    sl = acq if acq > 0 else max((x.get("shareAfterTrade") or 0) - (x.get("shareBeforeTrade") or 0), 0)
                    ev.append((pd.Timestamp(x["publicDate"]), -float(sl)))
            self.noibo[ma] = ev

    def ban_rong_noi_bo(self, ma, ngay):
        """Số cổ phiếu người nội bộ bán ròng (đã thực hiện) trong 12 tháng trước `ngay`; None nếu không có dữ liệu."""
        if ma not in self.noibo: return None
        return sum(v for d, v in self.noibo[ma] if ngay - pd.Timedelta(days=365) < d <= ngay)

    def cac_nam(self, ma, ngay, so_nam=5):
        """Các năm đã công bố tại `ngay`, mới nhất cuối."""
        ds = [(y, v) for y, v in self.nam.get(ma, {}).items() if v["hieu_luc"] <= ngay and all(k in v for k in ("kqkd", "cdkt", "lctt"))]
        return sorted(ds)[-so_nam:]

    def chi_so_moi_nhat(self, ma, ngay, n=1):
        ds = [r for d, r in self.chi_so.get(ma, []) if d <= ngay]
        return ds[-n:]


def _g(r, k):
    v = r.get(k)
    return float(v) if v is not None and np.isfinite(v) else np.nan


def _phep_thu_noi_bo(dl, ma, ngay, nguong=0.005):
    """Bán ròng của người nội bộ (đã thực hiện, 12 tháng) > 0,5% số cổ phiếu lưu hành thì không đạt. Chỉ đánh giá phần mua/bán, không có dữ liệu cầm cố hay gọi ký quỹ."""
    bn = dl.ban_rong_noi_bo(ma, ngay)
    cs = dl.chi_so_moi_nhat(ma, ngay)
    sh = _g(cs[-1], "numberOfSharesMktCap") if cs else np.nan
    if bn is None or not (sh and np.isfinite(sh) and sh > 0): return CHUA_DANH_GIA
    return bool(bn / sh <= nguong)


def phep_thu_phi_ngan_hang(dl, ma, ngay):
    """Trả về (kq dict, dữ liệu nhân tố) cho doanh nghiệp phi ngân hàng. kq[tên] in {True, False, CHUA_DANH_GIA}."""
    nam = dl.cac_nam(ma, ngay, 5)
    kq = {}
    if len(nam) < 3:
        return None, None
    d = [{"y": y, "isa3": _g(v["kqkd"], "isa3"), "lnst": _g(v["kqkd"], "isa22"), "pbt": _g(v["kqkd"], "isa16"),
          "lai": _g(v["kqkd"], "isa8"), "tn_khac": _g(v["kqkd"], "isa14"),
          "ocf": _g(v["lctt"], "cfa18"), "cotuc": _g(v["lctt"], "cfa32"),
          "pt": _g(v["cdkt"], "bsa8"), "tk": _g(v["cdkt"], "bsa15"), "vcsh": _g(v["cdkt"], "bsa78"),
          "vay": np.nansum([_g(v["cdkt"], "bsa56"), _g(v["cdkt"], "bsa71")])} for y, v in nam]
    df = pd.DataFrame(d).set_index("y")
    n4 = df.tail(4)
    # 1. OCF/LNST
    tong_ln = n4.lnst.sum()
    kq["1_ocf_lnst"] = bool(tong_ln > 0 and n4.ocf.sum() / tong_ln >= 0.8 and (n4.ocf < 0).sum() <= 1)
    # 2. phải thu + tồn kho tăng nhanh hơn doanh thu (3 năm)
    base, cur = df.iloc[-4:] .iloc[0], df.iloc[-1]
    ts0, ts1 = base.pt + base.tk, cur.pt + cur.tk
    if len(df) >= 4 and base.isa3 > 0 and ts0 > 0:
        tang_ts, tang_dt = ts1 / ts0 - 1, cur.isa3 / base.isa3 - 1
        kq["2_phai_thu_ton_kho"] = bool(tang_ts <= tang_dt + 0.15)
    else:
        kq["2_phai_thu_ton_kho"] = CHUA_DANH_GIA
    # 3. lãi từ khoản bất thường: thu nhập khác ròng / LNTT
    ty = (n4.tn_khac / n4.pbt).replace([np.inf, -np.inf], np.nan)
    kq["3_bat_thuong"] = bool(ty.mean() < 0.15) if ty.notna().sum() >= 2 else CHUA_DANH_GIA
    kq["4_ben_lien_quan"] = CHUA_DANH_GIA
    kq["5_kiem_toan"] = CHUA_DANH_GIA
    # 6. nợ vay, chi phí lãi: khả năng trả lãi >= 3 và nợ/VCSH <= 1,5 (nợ vay không tăng nhanh hơn lợi nhuận)
    lai = abs(cur.lai) if np.isfinite(cur.lai) else 0.0
    cover = (cur.pbt + lai) / lai if lai > 0 else np.inf
    de = cur.vay / cur.vcsh if cur.vcsh > 0 else np.inf
    kq["6_no_vay"] = bool(cover >= 3 and de <= 1.5)
    kq["7_noi_bo"] = _phep_thu_noi_bo(dl, ma, ngay)
    kq["0_bctc_moi"] = bool(nam[-1][1]["hieu_luc"] >= ngay - pd.Timedelta(days=450))
    so_nam_cotuc = int((df.cotuc < 0).tail(5).sum())
    kq["8_co_tuc_tien_mat"] = bool(so_nam_cotuc >= 4)
    roe = (n4.lnst / n4.vcsh).mean()
    nhan_to = {"roe": roe, "ocf_ln": n4.ocf.sum() / tong_ln if tong_ln > 0 else np.nan, "lnst": df.lnst.iloc[-1], "so_nam_cotuc": so_nam_cotuc}
    return kq, nhan_to


def phep_thu_ngan_hang(dl, ma, ngay):
    cs = dl.chi_so_moi_nhat(ma, ngay, 4)
    if len(cs) < 3:
        return None, None
    c = cs[-1]
    npl, bao_phu = _g(c, "npl"), abs(_g(c, "loansLossReservesToNPLs"))
    tang_tin_dung = _g(c, "loansGrowth")
    roe = np.nanmean([_g(x, "roe") for x in cs])
    kq = {"npl<=3%": bool(npl <= 0.03), "bao_phu>=70%": bool(bao_phu >= 0.7),
          "tang_tin_dung<=30%": bool(tang_tin_dung <= 0.30) if np.isfinite(tang_tin_dung) else CHUA_DANH_GIA,
          "roe>=10%": bool(roe >= 0.10), "co_tuc_tien_mat": CHUA_DANH_GIA, "7_noi_bo": _phep_thu_noi_bo(dl, ma, ngay),
          "0_bctc_moi": bool(dl.chi_so[ma][-1][0] >= ngay - pd.Timedelta(days=200)) if False else bool(any(d >= ngay - pd.Timedelta(days=200) for d, _ in dl.chi_so.get(ma, []) if d <= ngay))}
    return kq, {"roe": roe, "ocf_ln": np.nan, "lnst": np.nan, "so_nam_cotuc": np.nan}


def loc(dl, ma, ngay):
    """Trả về (đạt?, chi tiết, nhân tố). Quy tắc: mọi phép thử đánh giá được (trừ cổ tức) phải đạt; cổ tức: phi NH cần >=4/5 năm."""
    kq, nt = (phep_thu_ngan_hang if ma in NGAN_HANG else phep_thu_phi_ngan_hang)(dl, ma, ngay)
    if kq is None:
        return False, {"du_lieu": "thiếu lịch sử"}, None
    dat = all(v is True for k, v in kq.items() if v != CHUA_DANH_GIA)
    return dat, kq, nt


def diem_nhan_to(dl, gia_dong, vol, ds_ma, ngay, i, loc_fn=None):
    """Xếp hạng trung bình 3 nhân tố: chất lượng (ROE, OCF/LN), giá trị (suất sinh lời LN/vốn hóa), động lượng 12-1 và 6-1 tháng.
    gia_dong: DataFrame giá đóng cửa (nghìn đồng); i: chỉ số phiên."""
    hang = []
    for ma in ds_ma:
        dat, kq, nt = (loc_fn or loc)(dl, ma, ngay)
        if nt is None: continue
        c = gia_dong[ma]
        if i < 260 or not np.isfinite(c.iloc[i]) or not np.isfinite(c.iloc[i - 21]) or not np.isfinite(c.iloc[i - 252]):
            continue
        mom12 = c.iloc[i - 21] / c.iloc[i - 252] - 1
        mom6 = c.iloc[i - 21] / c.iloc[i - 126] - 1
        cs = dl.chi_so_moi_nhat(ma, ngay)
        sh = _g(cs[-1], "numberOfSharesMktCap") if cs else np.nan
        gia_tri = nt["lnst"] / (c.iloc[i] * 1000 * sh) if ma not in NGAN_HANG and sh and np.isfinite(sh) and nt["lnst"] == nt["lnst"] else np.nan
        if ma in NGAN_HANG and cs:
            pe = _g(cs[-1], "pe"); gia_tri = 1 / pe if pe and pe > 0 else np.nan
        hang.append({"ma": ma, "roe": nt["roe"], "ocf_ln": nt["ocf_ln"], "gia_tri": gia_tri, "mom": (mom12 + mom6) / 2})
    if not hang: return pd.DataFrame(columns=["diem"])
    df = pd.DataFrame(hang).set_index("ma")
    r = pd.DataFrame({"chat_luong": df[["roe", "ocf_ln"]].rank(pct=True).mean(axis=1), "gia_tri": df.gia_tri.rank(pct=True), "dong_luong": df.mom.rank(pct=True)})
    df["diem"] = r.mean(axis=1, skipna=True)
    return df.sort_values("diem", ascending=False)
