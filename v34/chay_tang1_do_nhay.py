import sys; sys.path.insert(0, "v34")
from khung_backtest import *
from loi_tang2 import *
from tang2_ttm import *
from tang2_phan_vi import tao_loc_phan_vi
from tang4_wyckoff import VeTinhWyckoff
from thong_ke import bootstrap_chu_dong
gia = nap_gia("data/gia"); dl = DuLieuTTM(); ds = [m for m in dl.nam if m in gia]; lpv = tao_loc_phan_vi(dl); cache = {}
def ghep(ten, a, b): return KetQua(ten, a.nav.add(b.nav, fill_value=0), a.dong_gop.add(b.dong_gop, fill_value=0), a.chi_phi + b.chi_phi, a.giao_dich_ban + b.giao_dich_ban, a.so_lenh_bi_chan + b.so_lenh_bi_chan)
def tui(tu, w, loai):
    e = Engine(gia, tu=tu, nap_hang_thang=10e6 * w)
    if loai == "etf": return e.chay("etf", MuaDeuETF())
    if loai == "t2": return e.chay("t2", LoiTang2(dl, 12, ds_ma=ds, loc_fn=lpv, ty_le_loi=0.5))
    if loai == "wy": return e.chay("wy", VeTinhWyckoff(dl, gia, ds, tin_hieu_kw={}, cache=cache))
tu = "2021-05-01"; e1 = Engine(gia, tu=tu); chuan = e1.chay("Mua đều E1VFVN30", MuaDeuETF()); ks = [chuan]
for loi in ("etf", "t2"):
    for wl in (0.90, 0.80, 0.75, 0.70):
        a, b = tui(tu, wl, loi), tui(tu, 1 - wl, "wy"); k = ghep(f"Lõi {'E1VFVN30' if loi=='etf' else 'T2 phân vị pha 50%'} {int(wl*100)}% + vệ tinh Wyckoff {int(round((1-wl)*100))}%", a, b); ks.append(k)
print(in_bang([chi_so(k) for k in ks]))
for k in ks[1:]: r = bootstrap_chu_dong(k, chuan); print(f"  {k.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}]")
