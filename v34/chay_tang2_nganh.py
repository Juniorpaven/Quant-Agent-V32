import sys, json, glob; sys.path.insert(0, "v34")
from khung_backtest import *
from loi_tang2 import *
from tang2_ttm import *
from tang2_phan_vi import tao_loc_phan_vi
from thong_ke import bootstrap_chu_dong
gia = nap_gia("data/gia"); dl = DuLieuTTM(); ds = [m for m in dl.nam if m in gia]; lpv = tao_loc_phan_vi(dl)
ng = {}
for f in glob.glob("data/ho_so/[A-Z]*.json"): d = json.load(open(f)); ng[d["ticker"]] = d.get("sector")
BT = [("T2 TTM, tối đa 3 mã/ngành", dict(loc_fn=loc_ttm, max_nganh=3, nganh=ng)), ("T2 phân vị, tối đa 3 mã/ngành", dict(loc_fn=lpv, max_nganh=3, nganh=ng)),
      ("T2 TTM, tối đa 2 mã/ngành", dict(loc_fn=loc_ttm, max_nganh=2, nganh=ng)), ("T2 TTM, 3 mã/ngành, pha 50% ETF", dict(loc_fn=loc_ttm, max_nganh=3, nganh=ng, ty_le_loi=0.5)),
      ("T2 phân vị, 3 mã/ngành, pha 50% ETF", dict(loc_fn=lpv, max_nganh=3, nganh=ng, ty_le_loi=0.5))]
for tu, den in (("2021-05-01", None), ("2021-05-01", "2023-12-31"), ("2024-01-01", None)):
    e = Engine(gia, tu=tu, den=den); chuan = e.chay("Mua đều E1VFVN30", MuaDeuETF()); ks = [chuan]
    for ten, kw in BT: ks.append(e.chay(ten, LoiTang2(dl, 12, ds_ma=ds, **kw)))
    print(f"\n### {tu} → {den or 'nay'}\n"); print(in_bang([chi_so(k) for k in ks]))
    if den is None and tu == "2021-05-01":
        for k in ks[1:]: r = bootstrap_chu_dong(k, chuan); print(f"  {k.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}]")
