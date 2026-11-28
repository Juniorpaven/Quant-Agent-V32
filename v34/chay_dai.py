"""Backtest tầng 2 trên mẫu dài (2010→nay): giá điều chỉnh Vietcap IQ, BCTC năm CafeF 2005–2025, cổ tức thật CafeF, nội bộ Vietcap.
Chuẩn: mua đều VN-Index giả lập (chỉ số, có phí; không có cổ tức) và rổ đều top 30 thanh khoản (cùng cơ sở giá). Bỏ nhân tố giá trị."""
import sys, glob, os; sys.path.insert(0, "v34")
import numpy as np, pandas as pd
import tang2_chon_ma as t2m
t2m.BO_GIA_TRI = True
from khung_backtest import *
from loi_tang2 import *
from loi_chung import *
from du_lieu_dai import *
from thong_ke import bootstrap_chu_dong
from tang3_mo_rong import LoiChiBao


def nap_dai():
    gia = {}
    for f in sorted(glob.glob("data/gia_dai/[A-Z]*.csv")):
        ma = os.path.basename(f)[:-4]; df = pd.read_csv(f, parse_dates=["Date"]).drop_duplicates("Date").set_index("Date").sort_index()
        gia[ma] = df
    cu = pd.read_csv("data/tham_do5/VNINDEX_truoc_2015.csv", parse_dates=["Date"]); moi = pd.read_csv("data/gia/VNINDEX.csv", parse_dates=["Date"])
    vn = pd.concat([cu, moi]).drop_duplicates("Date").sort_values("Date").set_index("Date"); vn = vn[vn.Close > 0]
    gia["VNINDEX"] = vn
    etf = vn.copy(); etf["Volume"] = 1e9
    for c in ("Open", "High", "Low", "Close"): etf[c] = vn[c] / 50
    gia["E1VFVN30"] = etf        # thay thế ETF = chỉ số giả lập (chưa có ETF trước 2014)
    return gia


def nguong_tk(d):  # đồng/phiên, bình quân 20 phiên
    return 3e9 if d.year <= 2014 else (5e9 if d.year <= 2017 else 10e9)


if __name__ == "__main__":
    gia = nap_dai(); dl = DuLieuDai(); ds = [m for m in dl.nam if m in gia and m not in ("VNINDEX", "E1VFVN30")]
    rong = [m for m in gia if m not in ("VNINDEX", "VN30", "E1VFVN30")]
    print("tập mã:", len(ds), "| giá:", len(rong))
    loc_fn = lambda d_, m, t: loc_dai(d_, m, t)
    for tu, den in (("2010-05-01", None), ("2010-05-01", "2014-12-31"), ("2015-01-01", "2020-12-31"), ("2021-01-01", None)):
        e = Engine(gia, tu=tu, den=den); e.nguong_fn = nguong_tk
        chuan = e.chay("Mua đều VN-Index giả lập", MuaDeuETF()); ks = [chuan]
        top30 = e.chay("Rổ đều top 30 thanh khoản (không lọc)", LoiDanhSach(chon_top_thanh_khoan(rong, 30), 30)); ks.append(top30)
        t2 = e.chay("T2 dài N=12", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai)); ks.append(t2)
        t2b = e.chay("T2 dài pha 50% chỉ số", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai, ty_le_loi=0.5)); ks.append(t2b)
        t2c = e.chay("T2 dài N=15", LoiTang2(dl, 15, ds_ma=ds, loc_fn=loc_dai)); ks.append(t2c)
        t2d = e.chay("T2 dài N=12 + tạm dừng MA200", LoiTang2(dl, 12, ds_ma=ds, loc_fn=loc_dai, chan_ma200=True)); ks.append(t2d)
        print(f"\n### {tu} → {den or 'nay'}\n"); print(in_bang([chi_so(k) for k in ks]))
        if den is None and tu == "2010-05-01":
            for k in ks[1:]:
                for ref, nm in ((chuan, "VN-Index giả lập"), (top30, "rổ top 30")):
                    if k is ref: continue
                    r = bootstrap_chu_dong(k, ref); print(f"  {k.ten} so với {nm}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}], p(≤0)={r['p_mot_phia(chu_dong<=0)']:.2f}")
