"""Khung backtest V34 (dùng chung cho mọi tầng).
Giả định theo mục 5 kế hoạch: phí 0,15%/chiều, thuế bán 0,1%, T+2,5 (mua phiên T bán được từ phiên T+2),
biên độ ±7%, lô 100, lọc thanh khoản, khớp ở giá mở cửa phiên kế tiếp (quyết định bằng dữ liệu đóng cửa phiên trước)."""
import glob, os
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

PHI = 0.0015
THUE_BAN = 0.001
LO = 100
BIEN_DO = 0.07
TAI_BAN_SAU = 2          # số phiên phải chờ trước khi bán
THANH_KHOAN_TOI_THIEU = 10e9  # đồng/phiên, bình quân 20 phiên
MIEN_THANH_KHOAN = {"E1VFVN30"}  # ETF: nạp tiền nhỏ, không cần lọc thanh khoản


def nap_gia(thu_muc):
    """Trả về dict ma -> DataFrame (index Date, cột Open High Low Close Volume). Giá nghìn đồng như Entrade."""
    out = {}
    for f in sorted(glob.glob(os.path.join(thu_muc, "*.csv"))):
        ma = os.path.basename(f)[:-4]
        df = pd.read_csv(f, parse_dates=["Date"]).drop_duplicates("Date").set_index("Date").sort_index()
        out[ma] = df
    return out


@dataclass
class KetQua:
    ten: str
    nav: pd.Series
    dong_gop: pd.Series
    chi_phi: float
    giao_dich_ban: float
    so_lenh_bi_chan: int
    nhat_ky: list = field(default_factory=list)


def _xirr(dong_tien):
    """dong_tien: list[(ngay, so_tien)] (âm = bỏ vào, dương = nhận). Trả về lãi suất năm."""
    ngay0 = dong_tien[0][0]
    t = np.array([(d - ngay0).days / 365.25 for d, _ in dong_tien])
    v = np.array([x for _, x in dong_tien])
    lo, hi = -0.99, 10.0
    f = lambda r: np.sum(v / (1 + r) ** t)
    if f(lo) * f(hi) > 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def chi_so(kq: KetQua):
    nav, dg = kq.nav, kq.dong_gop
    dong_tien = [(d, -x) for d, x in dg.items() if x > 0] + [(nav.index[-1], nav.iloc[-1])]
    irr = _xirr(dong_tien)
    # chuỗi lợi suất theo thời gian (TWR) loại bỏ dòng tiền nạp
    von_truoc = nav.shift(1)
    ret = ((nav - dg) / von_truoc - 1).replace([np.inf, -np.inf], np.nan).dropna()
    chuoi = (1 + ret).cumprod()
    mdd = float((chuoi / chuoi.cummax() - 1).min()) if len(chuoi) else float("nan")
    sharpe = float(ret.mean() / ret.std() * np.sqrt(250)) if ret.std() > 0 else float("nan")
    nam = (nav.index[-1] - nav.index[0]).days / 365.25
    von_bq = nav.mean()
    return {"Tên": kq.ten, "CAGR (XIRR)": irr, "MDD": mdd, "Sharpe": sharpe,
            "NAV cuối (triệu)": nav.iloc[-1] / 1e6, "Tổng nạp (triệu)": dg.sum() / 1e6,
            "Vòng quay bán/năm": kq.giao_dich_ban / von_bq / nam if nam > 0 else float("nan"),
            "Tổng chi phí (triệu)": kq.chi_phi / 1e6, "Lệnh bị chặn": kq.so_lenh_bi_chan}


class Engine:
    def __init__(self, gia, tu="2015-01-01", den=None, nap_hang_thang=10e6, von_dau=0.0):
        self.gia = gia
        full = gia["VNINDEX"].index
        self.cal = gia["VNINDEX"].loc[tu:den].index
        self.close_full = pd.DataFrame({m: d["Close"] for m, d in gia.items()}).reindex(full)
        self.off = full.get_loc(self.cal[0])
        self.open = pd.DataFrame({m: d["Open"] for m, d in gia.items()}).reindex(self.cal)
        self.close = pd.DataFrame({m: d["Close"] for m, d in gia.items()}).reindex(self.cal)
        self.vol = pd.DataFrame({m: d["Volume"] for m, d in gia.items()}).reindex(self.cal)
        self.gtgd20 = (self.close * self.vol * 1000).rolling(20, min_periods=10).mean()  # giá nghìn đồng
        self.nap = nap_hang_thang
        self.von_dau = von_dau

    def dat_duoc(self, ma, i):
        """Đủ thanh khoản và có giá tại phiên i."""
        if ma in MIEN_THANH_KHOAN: return True
        v = self.gtgd20[ma].iloc[i] if ma in self.gtgd20 else np.nan
        return np.isfinite(v) and v >= THANH_KHOAN_TOI_THIEU

    def chay(self, ten, chien_luoc, cho_phep_etf_thanh_khoan=False):
        """chien_luoc.muc_tieu(engine, i, vi_the) -> dict ma->tỷ trọng (tổng <=1, phần còn lại tiền mặt) hoặc None (không đổi).
        i là chỉ số phiên đã đóng cửa; lệnh khớp ở mở cửa phiên i+1."""
        cal = self.cal
        tien, vt, ngay_mua = self.von_dau, {}, {}  # vt: ma -> số cổ; ngay_mua: ma -> chỉ số phiên mua gần nhất
        nav, dg, chi_phi, ban_tong, chan = [], [], 0.0, 0.0, 0
        cho = None  # lệnh chờ khớp
        thang_truoc = None
        nhat_ky = []
        for i, d in enumerate(cal):
            nap_hom_nay = 0.0
            if (d.year, d.month) != thang_truoc:
                thang_truoc = (d.year, d.month)
                nap_hom_nay = self.nap if i > 0 or self.von_dau == 0 else 0
                tien += nap_hom_nay
            # khớp lệnh chờ ở giá mở cửa phiên i
            if cho is not None and i > 0:
                tc = self.close.iloc[i - 1]
                # bán trước, mua sau
                for ma, muc in cho["ban"].items():
                    po, ptc = self.open[ma].iloc[i], tc.get(ma, np.nan)
                    if not np.isfinite(po) or po <= ptc * (1 - BIEN_DO + 1e-3):
                        chan += 1; continue          # giá sàn: không bán được
                    if i - ngay_mua.get(ma, -9) < TAI_BAN_SAU:
                        chan += 1; continue          # T+2,5
                    sl = min(vt.get(ma, 0), int(muc // LO) * LO)
                    if sl <= 0: continue
                    gt = sl * po * 1000
                    phi = gt * (PHI + THUE_BAN)
                    tien += gt - phi; chi_phi += phi; ban_tong += gt
                    vt[ma] -= sl
                    if vt[ma] == 0: del vt[ma]
                for ma, ngan_sach in cho["mua"].items():
                    po, ptc = self.open[ma].iloc[i], tc.get(ma, np.nan)
                    if not np.isfinite(po) or po >= ptc * (1 + BIEN_DO - 1e-3):
                        chan += 1; continue          # giá trần: không mua được
                    sl = int(min(ngan_sach, tien) / (po * 1000 * (1 + PHI)) // LO) * LO
                    if sl <= 0: continue
                    gt = sl * po * 1000
                    phi = gt * PHI
                    tien -= gt + phi; chi_phi += phi
                    vt[ma] = vt.get(ma, 0) + sl
                    ngay_mua[ma] = i
                cho = None
            gia_tri = tien + sum(sl * self.close[m].iloc[i] * 1000 for m, sl in vt.items() if np.isfinite(self.close[m].iloc[i]))
            nav.append(gia_tri); dg.append(nap_hom_nay)
            # quyết định cho phiên sau
            if i < len(cal) - 1:
                vi_the = {m: sl * self.close[m].iloc[i] * 1000 for m, sl in vt.items()}
                mt = chien_luoc.muc_tieu(self, i, dict(vi_the), tien, gia_tri)
                if mt is not None:
                    cho = self._lap_lenh(mt, vi_the, tien, gia_tri, i)
                    nhat_ky.append((d, {k: round(v, 3) for k, v in mt.items()}))
        return KetQua(ten, pd.Series(nav, cal), pd.Series(dg, cal), chi_phi, ban_tong, chan, nhat_ky)

    def _lap_lenh(self, mt, vi_the, tien, nav, i):
        ban, mua = {}, {}
        for ma in set(vi_the) | set(mt):
            hien = vi_the.get(ma, 0.0)
            dich = mt.get(ma, 0.0) * nav
            if ma in mt and not self.dat_duoc(ma, i) and hien == 0:
                continue  # không mua mã thiếu thanh khoản
            chenh = dich - hien
            if abs(chenh) < 0.002 * nav:   # bỏ qua chênh lệch nhỏ để giảm vòng quay
                continue
            px = self.close[ma].iloc[i] * 1000
            if chenh < 0: ban[ma] = -chenh / px
            else: mua[ma] = chenh
        return {"ban": ban, "mua": mua}


# ---------- Chiến lược chuẩn ----------
class MuaDeuETF:
    """Chuẩn so sánh: mua đều hằng tháng một mã (E1VFVN30 hoặc VNINDEX không mua được -> chỉ dùng ETF)."""
    def __init__(self, ma="E1VFVN30"): self.ma = ma; self.thang = None
    def muc_tieu(self, eng, i, vi_the, tien, nav):
        d = eng.cal[i]
        if (d.year, d.month) == self.thang: return None
        self.thang = (d.year, d.month)
        return {self.ma: 1.0}


def chi_so_chi_so(gia, ma, tu, den=None, nap=10e6):
    """Mua đều VN-Index không phí (tham chiếu chỉ số)."""
    s = gia[ma]["Close"].loc[tu:den]
    thang = s.groupby([s.index.year, s.index.month]).head(1)
    so_don_vi = (nap / thang).sum()
    nav = pd.Series(0.0, s.index); dg = pd.Series(0.0, s.index)
    don_vi = 0.0
    for d, p in s.items():
        if d in thang.index:
            don_vi += nap / p; dg[d] = nap
        nav[d] = don_vi * p
    return KetQua(f"Mua đều {ma} (không phí)", nav, dg, 0.0, 0.0, 0)


def in_bang(ds):
    df = pd.DataFrame(ds).set_index("Tên")
    pc = ["CAGR (XIRR)", "MDD", "Vòng quay bán/năm"]
    out = df.copy()
    for c in pc: out[c] = (df[c] * 100).round(2).astype(str) + "%"
    for c in ["Sharpe", "NAV cuối (triệu)", "Tổng nạp (triệu)", "Tổng chi phí (triệu)"]: out[c] = df[c].round(2)
    return out.to_markdown() if hasattr(out, "to_markdown") else out.to_string()
