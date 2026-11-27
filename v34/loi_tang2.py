"""Chiến lược lõi tầng 2: giữ tối đa N mã đạt lọc chất lượng, rà quý, chỉ bán khi mã trượt lọc; nạp tiền hằng tháng chỉ mua thêm."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "v34")
from tang2_chon_ma import *

NGAY_RA_SOAT = {2: 15, 5: 15, 8: 15, 11: 15}  # tháng: ngày (sau mùa BCTC: quý +45 ngày)


class LoiTang2:
    def __init__(self, dl, n=12, ma_etf="E1VFVN30", chan_ma200=False, ds_ma=None, max_ngan_hang=None, ty_le_loi=1.0):
        self.dl, self.n, self.etf, self.chan = dl, n, ma_etf, chan_ma200
        self.max_nh, self.ty_le = max_ngan_hang, ty_le_loi
        self.ds_ma = ds_ma or [m for m in dl.nam]
        self.giu, self.thang_ra_soat, self.thang_nap, self.cache200 = [], None, None, None
        self.nhat_ky_chon = []

    def _duoi_ma200(self, eng, i):
        if self.cache200 is None:
            vn = eng.gia["VNINDEX"]["Close"].reindex(eng.cal).ffill()
            self.cache200 = (vn < vn.rolling(200).mean()).fillna(False)
        return bool(self.cache200.iloc[i])

    def _ra_soat(self, eng, i):
        d = eng.cal[i]
        dl = self.dl
        con_lai = []
        for ma in self.giu:
            dat, _, _ = loc(dl, ma, d)
            if dat: con_lai.append(ma)
        thoat = [m for m in self.giu if m not in con_lai]
        self.giu = con_lai
        if len(self.giu) < self.n:
            ung = [m for m in self.ds_ma if m in eng.close.columns and m not in self.giu and loc(dl, m, d)[0] and eng.dat_duoc(m, i)]
            if ung:
                bang = diem_nhan_to(dl, eng.close_full, eng.vol, ung, d, i + eng.off)
                for m in bang.index:
                    if len(self.giu) >= self.n: break
                    if self.max_nh is not None and m in NGAN_HANG and sum(x in NGAN_HANG for x in self.giu) >= self.max_nh: continue
                    self.giu.append(m)
        self.nhat_ky_chon.append((d.date(), list(self.giu), thoat))

    def muc_tieu(self, eng, i, vi_the, tien, nav):
        d = eng.cal[i]
        thang = (d.year, d.month)
        ra_soat = d.month in NGAY_RA_SOAT and d.day >= NGAY_RA_SOAT[d.month] and thang != self.thang_ra_soat
        dau_thang = thang != self.thang_nap
        if not ra_soat and not dau_thang:
            return None
        if ra_soat:
            self._ra_soat(eng, i); self.thang_ra_soat = thang
        self.thang_nap = thang
        o = max(self.n, 1)
        hien = {m: v / nav for m, v in vi_the.items()}
        muc = {m: hien[m] for m in hien if m in self.giu or m == self.etf}  # mã không còn trong lõi bị bán hết (trừ ETF)
        # khe chưa lấp -> ETF
        trong = o - len(self.giu)
        dich = {m: self.ty_le / o for m in self.giu}
        dich[self.etf] = dich.get(self.etf, 0) + self.ty_le * trong / o + (1 - self.ty_le)
        ngan_sach = 1.0 - sum(muc.values())
        if self.chan and self._duoi_ma200(eng, i):
            ngan_sach = 0.0
        thieu = {m: max(dich[m] - muc.get(m, 0.0), 0.0) for m in dich}
        tong_thieu = sum(thieu.values())
        if tong_thieu > 0 and ngan_sach > 0:
            he_so = min(1.0, ngan_sach / tong_thieu)
            for m, t in thieu.items():
                muc[m] = muc.get(m, 0.0) + t * he_so
        return {m: w for m, w in muc.items()}
