"""Chiến lược danh sách tổng quát: chon_fn(eng, i, giu) trả về danh sách mã mục tiêu (<= n). Nạp tiền hằng tháng chỉ mua thêm; mã rời danh sách bị bán."""
import numpy as np


class LoiDanhSach:
    def __init__(self, chon_fn, n=12, thang_ra_soat=(1, 4, 7, 10), ma_etf="E1VFVN30", tl_loi=1.0):
        self.chon, self.n, self.rs, self.etf, self.tl = chon_fn, n, set(thang_ra_soat), ma_etf, tl_loi
        self.giu, self.t_rs, self.t_nap = [], None, None

    def muc_tieu(self, eng, i, vi_the, tien, nav):
        d = eng.cal[i]; thang = (d.year, d.month)
        ra_soat = d.month in self.rs and thang != self.t_rs
        if not ra_soat and thang == self.t_nap: return None
        if ra_soat: self.giu = list(self.chon(eng, i, list(self.giu)))[: self.n]; self.t_rs = thang
        self.t_nap = thang
        hien = {m: v / nav for m, v in vi_the.items() if np.isfinite(v)}
        muc = {m: hien[m] for m in hien if m in self.giu or m == self.etf}
        dich = {m: self.tl / self.n for m in self.giu}
        dich[self.etf] = dich.get(self.etf, 0) + self.tl * (self.n - len(self.giu)) / self.n + (1 - self.tl)
        ngan_sach = 1.0 - sum(muc.values())
        thieu = {m: max(dich[m] - muc.get(m, 0.0), 0.0) for m in dich}; tt = sum(thieu.values())
        if tt > 0 and ngan_sach > 0:
            k = min(1.0, ngan_sach / tt)
            for m, t in thieu.items(): muc[m] = muc.get(m, 0.0) + t * k
        return muc


def chon_top_thanh_khoan(ds_ma, n=30):
    def f(eng, i, giu):
        g = eng.gtgd20.iloc[i]
        ok = [m for m in ds_ma if m in g.index and np.isfinite(g[m]) and g[m] >= 10e9 and np.isfinite(eng.close[m].iloc[i])]
        return sorted(ok, key=lambda m: -g[m])[:n]
    return f
