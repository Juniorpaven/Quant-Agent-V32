"""Dữ liệu do người dùng nhập tay (không có nguồn tự động): ý kiến kiểm toán, cầm cố cổ phiếu, lãi suất liên ngân hàng.
Chưa có file thì mọi phép thử tương ứng ghi 'không đánh giá được' (không tự gán 'đạt'). File mẫu: data/*.mau.csv."""
import os
import numpy as np, pandas as pd

XAU = ("ngoại trừ", "từ chối", "không thể đưa ra ý kiến", "trái ngược")


def doc_csv(duong_dan, cot):
    if not os.path.exists(duong_dan): return None
    df = pd.read_csv(duong_dan, comment="#")
    return df if all(c in df.columns for c in cot) else None


class DuLieuThuCong:
    def __init__(self, thu_muc="data"):
        self.kt = doc_csv(os.path.join(thu_muc, "kiem_toan_y_kien.csv"), ["ma", "nam", "y_kien"])
        self.cc = doc_csv(os.path.join(thu_muc, "cam_co.csv"), ["ma", "ngay", "ty_le_pct"])
        self.ls = doc_csv(os.path.join(thu_muc, "lai_suat_lnh.csv"), ["ngay", "lai_suat_qua_dem_pct"])
        if self.cc is not None: self.cc["ngay"] = pd.to_datetime(self.cc["ngay"])
        if self.ls is not None: self.ls["ngay"] = pd.to_datetime(self.ls["ngay"]); self.ls = self.ls.sort_values("ngay").set_index("ngay").lai_suat_qua_dem_pct

    def kiem_toan(self, ma, ngay):
        """True = ba năm gần nhất (đã công bố) không có ý kiến ngoại trừ/từ chối; False = có; None = không có dữ liệu cho mã này."""
        if self.kt is None: return None
        d = self.kt[self.kt.ma == ma]
        if d.empty: return None
        han = ngay.year - 1 if ngay >= pd.Timestamp(ngay.year, 4, 1) else ngay.year - 2      # năm tài chính mới nhất đã công bố
        d = d[(d.nam <= han) & (d.nam > han - 3)]
        if d.empty: return None
        return not any(any(x in str(k).lower() for x in XAU) for k in d.y_kien)

    def cam_co(self, ma, ngay, nguong=30.0):
        """True = tỷ lệ cổ phần bị cầm cố mới nhất (trong 12 tháng) dưới ngưỡng; False = từ ngưỡng trở lên; None = không có dữ liệu."""
        if self.cc is None: return None
        d = self.cc[(self.cc.ma == ma) & (self.cc.ngay <= ngay) & (self.cc.ngay > ngay - pd.Timedelta(days=365))]
        if d.empty: return None
        return bool(d.sort_values("ngay").ty_le_pct.iloc[-1] < nguong)

    def tin_hieu_lai_suat(self, chi_so_ngay, tang_toi_da=1.0, cua_so_tuan=13):
        """Series bool theo lịch (True = ĐƯỢC giải ngân). Tạm dừng khi lãi suất qua đêm (TB 4 tuần) tăng >= tang_toi_da điểm % so với 13 tuần trước. Không có dữ liệu thì trả None."""
        if self.ls is None or len(self.ls) < 20: return None
        w = self.ls.resample("W").last().ffill(); tb = w.rolling(4, min_periods=1).mean()
        xau = (tb - tb.shift(cua_so_tuan)) >= tang_toi_da
        return (~xau).reindex(chi_so_ngay, method="ffill").fillna(True)
