"""Kiểm tra độ vững của kết quả tầng 2 trên mẫu dài: chuẩn có cổ tức ước lượng, bỏ ngẫu nhiên 30% mã, bỏ 10 mã tăng mạnh nhất (hậu kiến), chọn ngẫu nhiên trong mã đạt lọc, trượt giá."""
import sys; sys.path.insert(0, "v34")
import numpy as np, pandas as pd
import tang2_chon_ma as t2m
t2m.BO_GIA_TRI = True
from khung_backtest import *
from loi_tang2 import *
from du_lieu_dai import *
from thong_ke import bootstrap_chu_dong
from chay_dai import nap_dai, nguong_tk

gia = nap_dai(); dl = DuLieuDai(); ds = [m for m in dl.nam if m in gia and m not in ("VNINDEX", "E1VFVN30")]
# chuẩn có cổ tức ước lượng: cộng 2,2%/năm (chênh lệch E1VFVN30 so với VN-Index giai đoạn 2015–2026)
gia_cd = dict(gia); etf = gia["E1VFVN30"].copy(); nam = (etf.index - etf.index[0]).days / 365.25
for c in ("Open", "High", "Low", "Close"): etf[c] = etf[c] * (1.022 ** nam)
gia_cd["E1VFVN30"] = etf
# 10 mã tăng mạnh nhất 2010-05 → nay (hậu kiến)
tt = {m: gia[m].Close.iloc[-1] / gia[m].Close.asof(pd.Timestamp("2010-05-04")) for m in ds if gia[m].index[0] <= pd.Timestamp("2010-05-04") and gia[m].index[-1] >= pd.Timestamp("2026-11-01")}
top10 = sorted(tt, key=tt.get, reverse=True)[:10]; print("10 mã tăng mạnh nhất (bỏ ra trong kiểm tra):", top10, flush=True)
for tu in ("2010-05-01", "2015-01-01"):
    e = Engine(gia, tu=tu); e.nguong_fn = nguong_tk; ecd = Engine(gia_cd, tu=tu); ecd.nguong_fn = nguong_tk
    def in1(k): c = chi_so(k); print(f"  [{tu}] {k.ten}: CAGR {c['CAGR (XIRR)']*100:.2f}%, MDD {c['MDD']*100:.1f}%, Sharpe {c['Sharpe']:.2f}", flush=True); return k
    chuan = in1(e.chay("Mua đều VN-Index giả lập", MuaDeuETF())); chuan_cd = in1(ecd.chay("Mua đều VN-Index + 2,2%/năm (cổ tức ước lượng)", MuaDeuETF()))
    ks = [chuan, chuan_cd]
    t2 = in1(e.chay("T2 dài N=12 (cơ sở)", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai))); ks.append(t2)
    ks.append(in1(e.chay("T2 dài N=12, bỏ 10 mã tăng mạnh nhất (hậu kiến)", LoiTang2(dl, 12, ds_ma=[m for m in ds if m not in top10], loc_fn=loc_dai))))
    sub = []
    for sd in range(3):
        rng = np.random.default_rng(100 + sd); chon = [m for m in ds if rng.random() < 0.7]
        k = in1(e.chay(f"bỏ ngẫu nhiên 30% mã #{sd}", LoiTang2(dl, 12, ds_ma=chon, loc_fn=loc_dai))); sub.append(chi_so(k))
    ng = [chi_so(in1(e.chay(f"ngẫu nhiên trong mã đạt lọc #{sd}", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai, xep="ngau_nhien", seed=sd)))) for sd in range(3)]
    ks.append(in1(e.chay("T2 chỉ ROE", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai, xep="roe"))))
    ts = Engine(gia, tu=tu, truot_gia=0.003); ts.nguong_fn = nguong_tk
    ks.append(in1(ts.chay("T2 dài N=12, trượt giá 0,3%", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai)))); ks.append(in1(ts.chay("VN-Index giả lập, trượt giá 0,3%", MuaDeuETF())))
    print(f"\n### {tu} → nay\n"); print(in_bang([chi_so(k) for k in ks]))
    for nm, lst in (("bỏ ngẫu nhiên 30% mã (4 lần)", sub), ("ngẫu nhiên trong mã đạt lọc (4 lần)", ng)):
        a = np.array([[x["CAGR (XIRR)"], x["MDD"]] for x in lst]); print(f"  {nm}: CAGR trung bình {a[:,0].mean()*100:.2f}% (min {a[:,0].min()*100:.2f}, max {a[:,0].max()*100:.2f}), MDD trung bình {a[:,1].mean()*100:.1f}%")
    for k in ks[2:5]:
        for ref in (chuan_cd,):
            r = bootstrap_chu_dong(k, ref); print(f"  {k.ten} so với {ref.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}], p(≤0)={r['p_mot_phia(chu_dong<=0)']:.2f}")
