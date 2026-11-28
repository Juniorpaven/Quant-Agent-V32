"""Backtest tầng 2 trên tập mã ĐẦY ĐỦ (HSX, HNX và mã đã hủy niêm yết; không chọn tay), mẫu dài từ 2010. Kết quả in ngay sau mỗi cấu hình."""
import sys; sys.path.insert(0, "v34")
import numpy as np, pandas as pd
import tang2_chon_ma as t2m
t2m.BO_GIA_TRI = True
from khung_backtest import *
from loi_tang2 import *
from loi_chung import *
from du_lieu_dai import *
from thong_ke import bootstrap_chu_dong
from chay_dai import nap_dai, nguong_tk

gia = nap_dai(); dl = DuLieuDai(); ds = [m for m in dl.nam if m in gia and m not in ("VNINDEX", "E1VFVN30")]
rong = [m for m in gia if m not in ("VNINDEX", "VN30", "E1VFVN30")]
da_huy = [m for m in ds if gia[m].index[-1] < pd.Timestamp("2026-10-01")]
print(f"tập mã: {len(ds)} có BCTC và giá | tổng mã có giá: {len(rong)} | ngừng giao dịch trước 10/2026: {len(da_huy)} ({len(da_huy)/len(ds)*100:.0f}%)", flush=True)
gia_cd = dict(gia); etf = gia["E1VFVN30"].copy(); nam = (etf.index - etf.index[0]).days / 365.25
for c in ("Open", "High", "Low", "Close"): etf[c] = etf[c] * (1.022 ** nam)
gia_cd["E1VFVN30"] = etf
tt = {m: gia[m].Close.iloc[-1] / gia[m].Close.asof(pd.Timestamp("2010-05-04")) for m in ds if gia[m].index[0] <= pd.Timestamp("2010-05-04") and gia[m].index[-1] >= pd.Timestamp("2026-11-01")}
top10 = sorted(tt, key=tt.get, reverse=True)[:10]; print("10 mã tăng mạnh nhất (bỏ ra trong kiểm tra hậu kiến):", top10, flush=True)
for tu in ("2010-05-01", "2015-01-01"):
    e = Engine(gia, tu=tu); e.nguong_fn = nguong_tk; ecd = Engine(gia_cd, tu=tu); ecd.nguong_fn = nguong_tk
    def in1(k): c = chi_so(k); print(f"  [{tu}] {k.ten}: CAGR {c['CAGR (XIRR)']*100:.2f}%, MDD {c['MDD']*100:.1f}%, Sharpe {c['Sharpe']:.2f}, vòng quay {c['Vòng quay bán/năm']*100:.0f}%", flush=True); return k
    chuan = in1(e.chay("Mua đều VN-Index giả lập", MuaDeuETF())); chuan_cd = in1(ecd.chay("Mua đều VN-Index + 2,2%/năm (cổ tức ước lượng)", MuaDeuETF()))
    top30 = in1(e.chay("Rổ đều top 30 thanh khoản (toàn thị trường, gồm mã đã hủy)", LoiDanhSach(chon_top_thanh_khoan(rong, 30), 30)))
    ks = [chuan, chuan_cd, top30]
    t2 = in1(e.chay("T2 N=12", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai))); ks.append(t2)
    ks.append(in1(e.chay("T2 N=15", LoiTang2(dl, 15, ds_ma=ds, loc_fn=loc_dai))))
    ks.append(in1(e.chay("T2 pha 50% chỉ số", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai, ty_le_loi=0.5))))
    ks.append(in1(e.chay("T2 N=12 + tạm dừng MA200", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai, chan_ma200=True))))
    ks.append(in1(e.chay("T2 N=12, bỏ 10 mã thắng lớn nhất (hậu kiến)", LoiTang2(dl, 12, ds_ma=[m for m in ds if m not in top10], loc_fn=loc_dai))))
    ng = [chi_so(in1(e.chay(f"ngẫu nhiên trong mã đạt lọc #{sd}", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai, xep="ngau_nhien", seed=sd)))) for sd in range(3)]
    ts = Engine(gia, tu=tu, truot_gia=0.003); ts.nguong_fn = nguong_tk; ks.append(in1(ts.chay("T2 N=12, trượt giá 0,3%", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai))))
    print(f"\n### {tu} → nay\n"); print(in_bang([chi_so(k) for k in ks]), flush=True)
    a = np.array([[x["CAGR (XIRR)"], x["MDD"]] for x in ng]); print(f"  ngẫu nhiên trong mã đạt lọc (3 lần): CAGR trung bình {a[:,0].mean()*100:.2f}% (min {a[:,0].min()*100:.2f}, max {a[:,0].max()*100:.2f})", flush=True)
    for k in (t2, ks[4], ks[5], ks[7]):
        for ref in (chuan_cd, top30):
            r = bootstrap_chu_dong(k, ref); print(f"  {k.ten} so với {ref.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}], p(≤0)={r['p_mot_phia(chu_dong<=0)']:.2f}", flush=True)
