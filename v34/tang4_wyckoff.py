"""Tầng 4: tín hiệu Wyckoff khung tuần cho vệ tinh. Lõi là E1VFVN30; vốn vệ tinh chưa dùng nằm trong lõi.
Điều kiện vào (chốt cuối tuần, khớp mở cửa phiên sau):
  - Vùng đi ngang >= 8 tuần (biên độ <= 30%) trước đó, VÀ một trong:
  A) Spring + Test: trong 1–4 tuần trước có tuần thủng hỗ trợ <= 5% rồi đóng cửa trên hỗ trợ; tuần này test: đáy không thấp hơn đáy Spring, khối lượng < 0,7 lần TB 10 tuần, đóng cửa trên hỗ trợ.
  B) SOS: đóng cửa vượt đỉnh vùng, khối lượng >= 1,5 lần TB 10 tuần.
Dừng lỗ: giá vào − 2 ATR14; bám theo: đỉnh đóng cửa − 3 ATR (lấy ATR lúc vào)."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "v34")
from tang2_chon_ma import loc

SAN_TUAN_MIN, BIEN_DO_VUNG = 8, 0.30


def tin_hieu_tuan(df, san_tuan=None, bien_do=None, sos_vr=1.5, spring_vr=0.7, che_do="ca_hai"):
    """df: giá ngày một mã. Trả về DataFrame index = ngày giao dịch cuối tuần, cột loai ('A'/'B'/''), vol_ratio."""
    san_tuan = san_tuan or SAN_TUAN_MIN; bien_do = bien_do or BIEN_DO_VUNG
    d = df.copy()
    tuan = d.groupby(d.index.to_period("W-FRI")).agg(O=("Open", "first"), H=("High", "max"), L=("Low", "min"), C=("Close", "last"), V=("Volume", "sum"), ngay=("Close", lambda s: s.index[-1]))
    out = []
    for k in range(san_tuan + 12, len(tuan)):
        w = tuan.iloc[k]
        vung = tuan.iloc[k - 1 - 26 - 1 if k > 28 else 0: k - 1]  # vùng gồm các tuần trước (tối đa 26)
        vung = tuan.iloc[max(0, k - 27): k - 1]
        if len(vung) < san_tuan: continue
        ho_tro, dinh = vung.L.min(), vung.H.max()
        if dinh / ho_tro - 1 > bien_do: continue
        tb_v = tuan.V.iloc[k - 10:k].mean()
        vr = w.V / tb_v if tb_v > 0 else np.nan
        loai = ""
        # SOS
        if che_do != "chi_spring" and w.C > dinh and vr >= sos_vr: loai = "B"
        elif che_do != "chi_sos":
            # Spring trong 1–4 tuần trước
            for j in range(k - 4, k):
                s = tuan.iloc[j]
                if s.L < ho_tro and s.L >= ho_tro * 0.95 and s.C > ho_tro:
                    if w.L >= s.L and vr < spring_vr and w.C > ho_tro: loai = "A"
                    break
        if loai: out.append((w.ngay, loai, vr))
    return pd.DataFrame(out, columns=["ngay", "loai", "vr"]).set_index("ngay") if out else pd.DataFrame(columns=["loai", "vr"])


def atr14(df):
    pc = df.Close.shift(1)
    tr = pd.concat([df.High - df.Low, (df.High - pc).abs(), (df.Low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(14).mean()


class VeTinhWyckoff:
    def __init__(self, dl, gia, ds_ma, ma_etf="E1VFVN30", ty_le_moi_ma=0.05, toi_da=5, he_so_dung=2.0, he_so_bam=3.0, chi_ma_dat_loc=True, tin_hieu_kw=None, cache=None):
        self.dl, self.gia, self.etf = dl, gia, ma_etf
        self.w, self.toi_da, self.k_stop, self.k_trail = ty_le_moi_ma, toi_da, he_so_dung, he_so_bam
        self.loc_ct = chi_ma_dat_loc
        kw = tin_hieu_kw or {}; khoa = tuple(sorted(kw.items()))
        if cache is not None and khoa in cache: self.tin_hieu = cache[khoa]
        else:
            self.tin_hieu = {m: tin_hieu_tuan(gia[m], **kw) for m in ds_ma if m in gia and len(gia[m]) > 300}
            if cache is not None: cache[khoa] = self.tin_hieu
        self.atr = {m: atr14(gia[m]) for m in self.tin_hieu}
        self.vt = {}            # ma -> {stop, cao, atr}
        self.thang, self.cache_loc = None, {}
        self.nhat_ky = []

    def _dat_loc(self, ma, d):
        k = (ma, d.year, d.month)
        if k not in self.cache_loc: self.cache_loc[k] = loc(self.dl, ma, d)[0]
        return self.cache_loc[k]

    def muc_tieu(self, eng, i, vi_the, tien, nav):
        d = eng.cal[i]
        doi = False
        # cập nhật dừng lỗ, thoát khi đóng cửa thủng
        for m in list(self.vt):
            c = eng.close[m].iloc[i]
            if not np.isfinite(c): continue
            p = self.vt[m]
            p["cao"] = max(p["cao"], c)
            p["stop"] = max(p["stop"], p["cao"] - self.k_trail * p["atr"])
            if c < p["stop"] and m in vi_the:
                del self.vt[m]; doi = True; self.nhat_ky.append((d.date(), "thoát", m))
        # vào lệnh vào cuối tuần
        la_cuoi_tuan = i + 1 < len(eng.cal) and eng.cal[i + 1].to_period("W-FRI") != d.to_period("W-FRI")
        if la_cuoi_tuan and len(self.vt) < self.toi_da:
            cho = []
            for m, th in self.tin_hieu.items():
                if m in self.vt or d not in th.index: continue
                if self.loc_ct and not self._dat_loc(m, d): continue
                if not eng.dat_duoc(m, i): continue
                cho.append((th.loc[d, "vr"] if th.loc[d, "loai"] == "B" else 0, m, th.loc[d, "loai"]))
            for _, m, loai in sorted(cho, reverse=True)[: self.toi_da - len(self.vt)]:
                a = self.atr[m].loc[d]; c = eng.close[m].iloc[i]
                if not np.isfinite(a) or a <= 0: continue
                self.vt[m] = {"stop": c - self.k_stop * a, "cao": c, "atr": a}; doi = True; self.nhat_ky.append((d.date(), "vào " + loai, m))
        thang = (d.year, d.month)
        if thang != self.thang: self.thang = thang; doi = True
        if not doi: return None
        hien = {m: v / nav for m, v in vi_the.items()}
        muc = {}
        for m in self.vt: muc[m] = hien.get(m, 0.0) if hien.get(m, 0.0) > 0 else self.w
        muc[self.etf] = max(0.0, 1.0 - sum(muc.values()))
        return muc
