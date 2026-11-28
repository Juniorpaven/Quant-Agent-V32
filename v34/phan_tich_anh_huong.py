"""Đo mức ảnh hưởng của ba mục thiếu dữ liệu: (1) cận trên lợi ích của chỉ báo dẫn trước (lãi suất liên ngân hàng) cho luật MA200;
(2) chi phí các vụ sụp đổ của mã đã được giữ trong lõi tầng 2 (phần mà ý kiến kiểm toán và cầm cố/ký quỹ có thể giúp tránh)."""
import sys; sys.path.insert(0, "v34")
import numpy as np, pandas as pd
import tang2_chon_ma as t2m
t2m.BO_GIA_TRI = True
from khung_backtest import *
from tang3_mo_rong import LoiChiBao, chuoi_tin_hieu
from chay_dai import nap_dai, nguong_tk


class LoiMaDan(LoiChiBao):
    """Luật MA200 tạm dừng nhưng biết trước tín hiệu k phiên (cận trên lợi ích của một chỉ báo dẫn trước hoàn hảo)."""
    def __init__(self, k, **kw): super().__init__("ma", "tam_dung", n=200, **kw); self.k = k
    def muc_tieu(self, eng, i, vi_the, tien, nav):
        if self.tt is None: self.tt = chuoi_tin_hieu(eng, "ma", n=200).shift(-self.k).fillna(True) if self.k else chuoi_tin_hieu(eng, "ma", n=200)
        return super().muc_tieu(eng, i, vi_the, tien, nav)


gia_day_du = nap_dai()
gia = {"VNINDEX": gia_day_du["VNINDEX"], "E1VFVN30": gia_day_du["E1VFVN30"]}
print("=== (1) Chỉ báo dẫn trước hoàn hảo cho luật MA200 (cận trên lợi ích của lãi suất liên ngân hàng) ===", flush=True)
vn = gia["VNINDEX"].Close; ma = vn.rolling(200).mean(); duoi = (vn < ma)
# các đợt giảm lớn: đỉnh, ngày cắt xuống MA200, đáy
rows = []; cao = vn.expanding().max()
for ten, a, b in (("2008", "2007-01-01", "2009-06-30"), ("2011", "2010-10-01", "2012-01-31"), ("2018", "2018-03-01", "2018-12-31"), ("2020", "2020-01-01", "2020-04-30"), ("2022", "2022-03-01", "2022-12-31")):
    v = vn.loc[a:b]; dinh = v.idxmax(); day = v.loc[dinh:].idxmin()
    cat = duoi.loc[dinh:day]; ngay_cat = cat.index[cat.values.argmax()] if cat.any() else None
    rows.append((ten, dinh.date(), ngay_cat.date() if ngay_cat is not None else None, day.date(), round(float(vn.loc[ngay_cat] / vn.loc[dinh] - 1) * 100, 1) if ngay_cat is not None else None, round(float(vn.loc[day] / vn.loc[dinh] - 1) * 100, 1)))
print(pd.DataFrame(rows, columns=["đợt", "đỉnh", "ngày cắt MA200", "đáy", "% giảm đã xảy ra tại ngày cắt", "% giảm đến đáy"]).to_string(index=False), flush=True)
for tu in ("2001-01-01", "2010-05-01", "2015-01-01"):
    e = Engine(gia, tu=tu); ds = []
    for k in (0, 20, 40, 60, 120):
        r = chi_so(e.chay(f"MA200 biết trước {k} phiên", LoiMaDan(k))); ds.append(r)
    chuan = chi_so(e.chay("Mua đều chỉ số (không luật)", MuaDeuETF()))
    print(f"\n--- {tu} → nay (chuẩn không luật: CAGR {chuan['CAGR (XIRR)']*100:.2f}%, MDD {chuan['MDD']*100:.1f}%)", flush=True)
    for r in ds: print(f"  {r['Tên']}: CAGR {r['CAGR (XIRR)']*100:.2f}% ({(r['CAGR (XIRR)']-chuan['CAGR (XIRR)'])*100:+.2f} điểm so với không luật), MDD {r['MDD']*100:.1f}%", flush=True)

print("\n=== (2) Chi phí các vụ sụp đổ của mã đã giữ trong lõi tầng 2 (N=12, 2010→nay, tập mã đầy đủ) ===", flush=True)
from loi_tang2 import *
from du_lieu_dai import *
dl = DuLieuDai(); ds = [m for m in dl.nam if m in gia_day_du and m not in ("VNINDEX", "E1VFVN30")]
e = Engine(gia_day_du, tu="2010-05-01"); e.nguong_fn = nguong_tk
st = LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai); kq = e.chay("T2", st); c = chi_so(kq)
print(f"T2 N=12: CAGR {c['CAGR (XIRR)']*100:.2f}%, MDD {c['MDD']*100:.1f}%", flush=True)
nam_tong = (e.cal[-1] - e.cal[0]).days / 365.25
dang_giu = {}; episodes = []
for ngay, giu, thoat in st.nhat_ky_chon:
    ngay = pd.Timestamp(ngay)
    for m in list(dang_giu):
        if m not in giu: episodes.append((m, dang_giu.pop(m), ngay))
    for m in giu:
        if m not in dang_giu: dang_giu[m] = ngay
for m, d0 in dang_giu.items(): episodes.append((m, d0, e.cal[-1]))
res = []
for m, d0, d1 in episodes:
    s = gia_day_du[m].Close.loc[d0:d1]
    if len(s) < 2: continue
    huy = gia_day_du[m].index[-1] < min(d1, e.cal[-1]) - pd.Timedelta(days=15)    # dữ liệu giá dừng trước khi thoát: ngừng giao dịch
    tong = -1.0 if huy else float(s.iloc[-1] / s.iloc[0] - 1)
    tt = float((s / s.iloc[0]).min() - 1)
    res.append((m, d0.date(), d1.date(), tong, tt, huy))
df = pd.DataFrame(res, columns=["ma", "vao", "ra", "loi_suat", "sut_giam_toi_da", "ngung_giao_dich"])
sap = df[(df.loi_suat <= -0.5) | df.ngung_giao_dich]
print(f"Số lượt giữ (mã × lần vào): {len(df)} | mã khác nhau: {df.ma.nunique()} | lượt kết thúc lỗ ≥50% hoặc ngừng giao dịch: {len(sap)} ({len(sap)/len(df)*100:.1f}%) | lượt lỗ ≥30%: {int((df.loi_suat <= -0.3).sum())}", flush=True)
print(sap.sort_values("loi_suat").to_string(index=False), flush=True)
chi_phi = float((sap.loi_suat.clip(lower=-1) / 12).sum()) / nam_tong * 100
print(f"Chi phí gần đúng của các vụ sụp đổ: ≈ {chi_phi:.2f}% NAV mỗi năm (tỷ trọng 1/12 mỗi mã), tức tối đa {abs(chi_phi):.2f} điểm %/năm mà ý kiến kiểm toán và cầm cố có thể giúp tránh (cận trên, nếu chặn được toàn bộ)", flush=True)
print(f"Với mốc 'lỗ ≥30%': ≈ {float((df[df.loi_suat <= -0.3].loi_suat / 12).sum()) / nam_tong * 100:.2f}% NAV/năm", flush=True)
