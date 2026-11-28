import sys; sys.path.insert(0, "v34")
from khung_backtest import *
from loi_tang2 import *
from tang2_ttm import *
from tang2_phan_vi import tao_loc_phan_vi
from thong_ke import bootstrap_chu_dong
gia = nap_gia("data/gia"); dl = DuLieuTTM(); ds = [m for m in dl.nam if m in gia]
lpv = tao_loc_phan_vi(dl)
def bien_the(e):
    return [("T2 (bộ lọc năm, cơ sở)", dict()), ("T2 TTM + phép thử 4,5 thay thế", dict(loc_fn=loc_ttm)), ("T2 lọc phân vị (TTM)", dict(loc_fn=lpv)),
            ("T2 TTM, trần 4 ngân hàng", dict(loc_fn=loc_ttm, max_ngan_hang=4)), ("T2 phân vị, trần 4 ngân hàng", dict(loc_fn=lpv, max_ngan_hang=4)),
            ("T2 TTM pha 50% ETF", dict(loc_fn=loc_ttm, ty_le_loi=0.5)), ("T2 phân vị pha 50% ETF", dict(loc_fn=lpv, ty_le_loi=0.5)), ("T2 phân vị N=15", dict(loc_fn=lpv, n=15))]
for tu, den in (("2021-05-01", None), ("2021-05-01", "2023-12-31"), ("2024-01-01", None)):
    e = Engine(gia, tu=tu, den=den); chuan = e.chay("Mua đều E1VFVN30", MuaDeuETF()); ks = [chuan]
    for ten, kw in bien_the(e):
        n = kw.pop("n", 12); ks.append(e.chay(ten, LoiTang2(dl, n, ds_ma=ds, **kw)))
    print(f"\n### {tu} → {den or 'nay'}\n"); print(in_bang([chi_so(k) for k in ks]))
    if den is None and tu == "2021-05-01":
        for k in ks[1:]:
            r = bootstrap_chu_dong(k, chuan); print(f"  {k.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}], p(≤0)={r['p_mot_phia(chu_dong<=0)']:.2f}")
