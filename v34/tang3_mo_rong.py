"""Tầng 3 mở rộng: chỉ báo độ rộng và biến động, ngoài VN-Index so với MA. Mọi luật đều là 'tạm dừng mua' (không bán) hoặc 'có bán' về 50%."""
import numpy as np, pandas as pd


def chuoi_tin_hieu(eng, loai, **kw):
    """Trả về Series bool (True = ĐƯỢC giải ngân) theo lịch eng.cal."""
    vn = eng.gia["VNINDEX"]["Close"].reindex(eng.close_full.index).ffill()
    if loai == "ma":
        n = kw.get("n", 200); s = vn > vn.rolling(n).mean()
    elif loai == "do_rong":
        cot = [m for m in eng.close_full.columns if m not in ("VNINDEX", "VN30", "E1VFVN30")]
        c = eng.close_full[cot]; tren = (c > c.rolling(kw.get("n", 200), min_periods=150).mean()).where(c.notna() & c.rolling(kw.get("n", 200), min_periods=150).mean().notna())
        s = tren.mean(axis=1) >= kw.get("nguong", 0.40)
    elif loai == "bien_dong":
        r = np.log(vn).diff(); v20 = r.rolling(20).std() * np.sqrt(250); s = v20 <= kw.get("he_so", 1.5) * v20.rolling(250, min_periods=120).median()
    elif loai == "ma_va_do_rong":
        a = chuoi_tin_hieu(eng, "ma", n=200); b = chuoi_tin_hieu(eng, "do_rong", n=200, nguong=0.40); s = a | b   # chỉ dừng khi cả hai cùng xấu
    elif loai == "ma_hoac_do_rong":
        a = chuoi_tin_hieu(eng, "ma", n=200); b = chuoi_tin_hieu(eng, "do_rong", n=200, nguong=0.40); s = a & b   # dừng khi một trong hai xấu
    return s.fillna(True).reindex(eng.close_full.index).ffill().fillna(True)


class LoiChiBao:
    def __init__(self, loai, che_do="tam_dung", ty_le_duoi=0.5, ma="E1VFVN30", **kw):
        self.loai, self.che, self.tl, self.ma, self.kw = loai, che_do, ty_le_duoi, ma, kw; self.tt = None; self.thang = None
    def muc_tieu(self, eng, i, vi_the, tien, nav):
        if self.tt is None: self.tt = chuoi_tin_hieu(eng, self.loai, **self.kw)
        d = eng.cal[i]
        if d.weekday() != 4 and (d.year, d.month) == self.thang: return None
        self.thang = (d.year, d.month)
        tot = bool(self.tt.iloc[i + eng.off])
        if tot: return {self.ma: 1.0}
        if self.che == "ban_mua": return {self.ma: self.tl}
        hien = vi_the.get(self.ma, 0.0); return {self.ma: max(self.tl * nav, hien) / nav}
