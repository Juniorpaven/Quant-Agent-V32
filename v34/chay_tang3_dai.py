"""Tầng 3 trên chuỗi dài: mua đều trực tiếp trên VN-Index (giả lập, giá chia 50 để mua được lô 100) từ 2001, gồm khủng hoảng 2008 và 2011."""
import sys; sys.path.insert(0, "v34")
import pandas as pd
from khung_backtest import *
from tang3_mo_rong import LoiChiBao
from thong_ke import bootstrap_chu_dong
cu = pd.read_csv("data/tham_do5/VNINDEX_truoc_2015.csv", parse_dates=["Date"]); moi = pd.read_csv("data/gia/VNINDEX.csv", parse_dates=["Date"])
vn = pd.concat([cu, moi]).drop_duplicates("Date").sort_values("Date").set_index("Date"); vn = vn[vn.Close > 0]
vn["Volume"] = 1e9  # chỉ số: miễn lọc thanh khoản
chia = vn.copy()
for c in ("Open", "High", "Low", "Close"): chia[c] = vn[c] / 50
gia = {"VNINDEX": chia, "E1VFVN30": chia}
print("VN-Index:", vn.index.min().date(), "→", vn.index.max().date(), len(vn), "phiên")
RULES = [("MA150 tạm dừng", ("ma", "tam_dung", dict(n=150))), ("MA200 tạm dừng", ("ma", "tam_dung", dict(n=200))), ("MA250 tạm dừng", ("ma", "tam_dung", dict(n=250))),
         ("MA200 có bán 50%", ("ma", "ban_mua", dict(n=200))), ("Biến động>1,5 lần tạm dừng", ("bien_dong", "tam_dung", dict(he_so=1.5)))]
for tu, den in (("2001-01-01", None), ("2001-01-01", "2014-12-31"), ("2015-01-01", None)):
    e = Engine(gia, tu=tu, den=den); chuan = e.chay("Mua đều VN-Index (giả lập, có phí)", MuaDeuETF()); ks = [chuan] + [e.chay(t, LoiChiBao(sp[0], sp[1], **sp[2])) for t, sp in RULES]
    print(f"\n### {tu} → {den or 'nay'}\n"); print(in_bang([chi_so(k) for k in ks]))
    if den is None and tu == "2001-01-01":
        for k in ks[1:]: r = bootstrap_chu_dong(k, chuan); print(f"  {k.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}], p(≤0)={r['p_mot_phia(chu_dong<=0)']:.2f}")
