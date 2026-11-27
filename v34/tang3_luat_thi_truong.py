"""Tầng 3: luật thị trường VN-Index so với MA200, áp lên lõi (tạm dùng E1VFVN30 làm lõi vì chưa có tầng 2)."""
import sys, pandas as pd
sys.path.insert(0, "v34")
from khung_backtest import *


class LoiMA200:
    """che_do 'ban_mua': dưới MA thì hạ tỷ trọng lõi về `ty_le_duoi` NAV (có bán).
       che_do 'tam_dung': dưới MA thì không mua thêm (không bán). Quyết định hằng tuần (thứ Sáu) hoặc đầu tháng."""
    def __init__(self, ma_cua_so=200, ty_le_duoi=0.5, che_do="ban_mua", ma="E1VFVN30"):
        self.n, self.ty_le, self.che_do, self.ma = ma_cua_so, ty_le_duoi, che_do, ma
        self.cache = None
    def muc_tieu(self, eng, i, vi_the, tien, nav):
        if self.cache is None:
            vn = eng.gia["VNINDEX"]["Close"].reindex(eng.cal).ffill()
            self.cache = (vn > vn.rolling(self.n).mean()).fillna(True)
            self.thang = None
        d = eng.cal[i]
        if d.weekday() != 4 and (d.year, d.month) == self.thang: return None
        self.thang = (d.year, d.month)
        tren = bool(self.cache.iloc[i])
        w = 1.0 if tren else self.ty_le
        if self.che_do == "tam_dung":
            hien = vi_the.get(self.ma, 0.0)
            w = max(w * nav, hien) / nav if not tren else 1.0
        return {self.ma: w}
