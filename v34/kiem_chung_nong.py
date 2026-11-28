"""Kiểm chứng ba câu hỏi, mẫu 2010→nay, tập mã đầy đủ (gồm mã đã hủy; mã ngừng giao dịch trước mốc tính -100%):
(a) phép thử nội bộ (bán ròng 12 tháng) có tách được mã tăng yếu hơn không; (b) mã 'chạy nóng' có tăng yếu hơn sau đó không;
(c) thị trường 'hưng phấn' (giá trị giao dịch cao và VN-Index xa MA200) có dự báo lợi suất thấp không, và luật tạm dừng mua theo nó có giúp DCA không.
Ngưỡng đặt trước: nóng = tăng 3 tháng >= 30% hoặc 12 tháng >= 100%; hưng phấn = giao dịch 20 phiên >= 1,5 lần trung vị 250 phiên và VN-Index cao hơn MA200 >= 10%."""
import sys; sys.path.insert(0, "v34")
import numpy as np, pandas as pd
import tang2_chon_ma as t2m
t2m.BO_GIA_TRI = True
from khung_backtest import *
from du_lieu_dai import *
from loi_tang2 import *
from tang3_mo_rong import LoiChiBao
from chay_dai import nap_dai, nguong_tk

gia = nap_dai(); dl = DuLieuDai(); cal = gia["VNINDEX"].index
ds = [m for m in dl.nam if m in gia and m not in ("VNINDEX", "E1VFVN30")]
close = pd.DataFrame({m: gia[m].Close for m in ds}).reindex(cal); cf = close.ffill(limit=10)
vol = pd.DataFrame({m: gia[m].Volume for m in ds}).reindex(cal)
gtgd = (cf * vol * 1000).rolling(20, min_periods=10).mean()
ket = {m: gia[m].index[-1] for m in ds}; HET = pd.Timestamp("2026-10-01")


def dau_ky(thang, tu=2011, den=2025):
    out = []
    for y in range(tu, den + 1):
        for t in thang:
            ng = cal[(cal.year == y) & (cal.month == t)]
            if len(ng): out.append(cal.get_loc(ng[0]))
    return out


def fwd(m, i, h):
    if i + h >= len(cal): return np.nan
    p0, p1 = cf[m].iloc[i], cf[m].iloc[i + h]
    if not np.isfinite(p0) or p0 <= 0: return np.nan
    if np.isfinite(p1): return p1 / p0 - 1
    return -1.0 if (ket[m] < cal[i + h] - pd.Timedelta(days=15) and ket[m] < HET) else np.nan


def khoi(diff, khoi=4, n=4000, seed=1):
    x = np.array([v for v in diff if np.isfinite(v)]); T = len(x); rng = np.random.default_rng(seed); tb = []
    for _ in range(n):
        st = rng.integers(0, T, int(np.ceil(T / khoi))); tb.append(np.concatenate([x[(s + np.arange(khoi)) % T] for s in st])[:T].mean())
    tb = np.array(tb); return x.mean(), np.percentile(tb, 2.5), np.percentile(tb, 97.5), float((tb <= 0).mean()), T


def in_kq(ten, nhom_a, nhom_b, tenA, tenB, kh=4):
    d = [a - b for a, b in zip(nhom_a, nhom_b) if np.isfinite(a) and np.isfinite(b)]
    m, lo, hi, p, T = khoi(d, kh)
    print(f"  {ten}: {tenA} {np.nanmean(nhom_a)*100:+.1f}% | {tenB} {np.nanmean(nhom_b)*100:+.1f}% | chênh {m*100:+.2f} điểm, CI95 [{lo*100:+.1f}, {hi*100:+.1f}], p(chênh<=0)={p:.2f}, {T} mốc", flush=True)


print("=== (a) Phép thử nội bộ: lợi suất 12 tháng sau (ngày xét: đầu tháng 2, 5, 8, 11) ===", flush=True)
A, B, C, D, nA, nB = [], [], [], [], [], []
for i in dau_ky((2, 5, 8, 11), 2012, 2025):
    d = cal[i]; ung = [m for m in ds if np.isfinite(close[m].iloc[i]) and gtgd[m].iloc[i] >= nguong_tk(d)]
    ga, gb, gc, gd = [], [], [], []
    for m in ung:
        ok, kq, nt = loc_dai(dl, m, d)
        if nt is None: continue
        r = fwd(m, i, 250)
        if not np.isfinite(r): continue
        khac = all(v is True for k, v in kq.items() if k != "7_noi_bo" and v != t2m.CHUA_DANH_GIA); t7 = kq.get("7_noi_bo")
        if t7 is True: gc.append(r)
        if t7 is False: gd.append(r)
        if khac and t7 is True: ga.append(r)
        if khac and t7 is False: gb.append(r)
    A.append(np.mean(ga) if ga else np.nan); B.append(np.mean(gb) if gb else np.nan); C.append(np.mean(gc) if gc else np.nan); D.append(np.mean(gd) if gd else np.nan); nA.append(len(ga)); nB.append(len(gb))
print(f"  số mã trung bình mỗi mốc: đạt các phép thử khác và không bị cờ nội bộ {np.mean(nA):.1f}; bị cờ nội bộ {np.mean(nB):.1f}", flush=True)
in_kq("Trong số mã đạt các phép thử khác", A, B, "không cờ nội bộ", "bị cờ nội bộ")
in_kq("Toàn bộ mã thanh khoản", C, D, "không cờ nội bộ", "bị cờ nội bộ")

print("\n=== (b) Mã 'chạy nóng' (tăng 3 tháng >= 30% hoặc 12 tháng >= 100%): lợi suất sau đó (đầu mỗi tháng) ===", flush=True)
for h, ten in ((63, "3 tháng"), (126, "6 tháng"), (250, "12 tháng")):
    N, K, Nq, Kq = [], [], [], []
    for i in dau_ky(range(1, 13), 2011, 2025):
        d = cal[i]
        if i < 260: continue
        nong, binh, nongq, binhq = [], [], [], []
        for m in ds:
            if not (np.isfinite(close[m].iloc[i]) and gtgd[m].iloc[i] >= nguong_tk(d)): continue
            p3, p12 = cf[m].iloc[i - 63], cf[m].iloc[i - 250]
            if not (np.isfinite(p3) and np.isfinite(p12) and p3 > 0 and p12 > 0): continue
            r = fwd(m, i, h)
            if not np.isfinite(r): continue
            hot = (cf[m].iloc[i] / p3 - 1 >= 0.30) or (cf[m].iloc[i] / p12 - 1 >= 1.0)
            (nong if hot else binh).append(r)
        N.append(np.mean(nong) if len(nong) >= 3 else np.nan); K.append(np.mean(binh) if binh else np.nan)
    in_kq(f"Sau {ten}", N, K, "mã chạy nóng", "mã còn lại", 6)

print("\n=== (c) Thị trường hưng phấn: VN-Index sau các ngày có cờ (từ 2010) ===", flush=True)
vn = gia["VNINDEX"]; v20 = vn.Volume.rolling(20).mean(); med = v20.rolling(250, min_periods=120).median()
ty_le = v20 / med; xa = vn.Close / vn.Close.rolling(200).mean() - 1
def co(ten, cond):
    cond = cond & (vn.index >= "2010-01-01"); idx = np.where(cond.values)[0]
    ep = int((np.diff(idx) > 20).sum() + 1) if len(idx) else 0
    out = f"  {ten}: {len(idx)} ngày, {ep} đợt"
    for h in (60, 120, 250):
        fr = (vn.Close.shift(-h) / vn.Close - 1); tc = fr[(vn.index >= "2010-01-01")]; fl = fr[cond]
        out += f" | sau {h} phiên: có cờ {fl.mean()*100:+.1f}% (n={fl.notna().sum()}) so với mọi ngày {tc.mean()*100:+.1f}%"
    print(out, flush=True)
co("Hưng phấn (giao dịch >=1,5 lần và cao hơn MA200 >=10%) [đặt trước]", (ty_le >= 1.5) & (xa >= 0.10))
co("Chỉ giao dịch >= 2 lần trung vị", ty_le >= 2.0)
co("Chỉ cao hơn MA200 >= 15%", xa >= 0.15)
co("Chỉ cao hơn MA200 >= 10%", xa >= 0.10)

print("\n=== (c2) Luật tạm dừng mua khi thị trường hưng phấn (DCA trên chỉ số giả lập, có phí) ===", flush=True)
g2 = {"VNINDEX": gia["VNINDEX"], "E1VFVN30": gia["E1VFVN30"]}
class LoiTinHieu(LoiChiBao):
    def __init__(self, serie, ty_le_duoi): super().__init__("ma", "tam_dung", ty_le_duoi=ty_le_duoi, n=200); self.serie = serie
    def muc_tieu(self, eng, i, vi_the, tien, nav):
        if self.tt is None: self.tt = self.serie.reindex(eng.close_full.index).fillna(True)
        return super().muc_tieu(eng, i, vi_the, tien, nav)
duoc = ~((ty_le >= 1.5) & (xa >= 0.10))
for tu in ("2010-05-01", "2015-01-01"):
    e = Engine(g2, tu=tu); r0 = chi_so(e.chay("không luật", MuaDeuETF())); r1 = chi_so(e.chay("MA200", LoiChiBao("ma", "tam_dung", n=200))); r2 = chi_so(e.chay("hưng phấn", LoiTinHieu(duoc, 0.0)))
    print(f"  {tu}→: không luật CAGR {r0['CAGR (XIRR)']*100:.2f}% MDD {r0['MDD']*100:.1f}% | MA200 {r1['CAGR (XIRR)']*100:.2f}% | tạm dừng khi hưng phấn {r2['CAGR (XIRR)']*100:.2f}% MDD {r2['MDD']*100:.1f}% ({(r2['CAGR (XIRR)']-r0['CAGR (XIRR)'])*100:+.2f} điểm so với không luật)", flush=True)

print("\n=== (a2) Bỏ phép thử nội bộ khỏi lõi tầng 2 (N=12, tập mã đầy đủ) ===", flush=True)
bo7 = lambda d_, m, t: (lambda ok_kq: (all(v is True for k, v in ok_kq[1].items() if k != "7_noi_bo" and v != t2m.CHUA_DANH_GIA) if ok_kq[2] is not None else False, ok_kq[1], ok_kq[2]))(loc_dai(d_, m, t))
for tu in ("2010-05-01", "2015-01-01"):
    e = Engine(gia, tu=tu); e.nguong_fn = nguong_tk
    c0 = chi_so(e.chay("có", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai))); c1 = chi_so(e.chay("bỏ", LoiTang2(dl, 12, ds_ma=ds, loc_fn=bo7)))
    print(f"  {tu}→: có phép thử nội bộ CAGR {c0['CAGR (XIRR)']*100:.2f}% MDD {c0['MDD']*100:.1f}% | bỏ phép thử CAGR {c1['CAGR (XIRR)']*100:.2f}% MDD {c1['MDD']*100:.1f}% ({(c0['CAGR (XIRR)']-c1['CAGR (XIRR)'])*100:+.2f} điểm nhờ phép thử)", flush=True)
