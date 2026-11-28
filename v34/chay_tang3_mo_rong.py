import sys; sys.path.insert(0, "v34")
import pandas as pd
from khung_backtest import *
from tang3_mo_rong import LoiChiBao
from thong_ke import bootstrap_chu_dong
gia = nap_gia("data/gia")
RULES = [("MA150 tạm dừng", ("ma", "tam_dung", dict(n=150))), ("MA200 tạm dừng", ("ma", "tam_dung", dict(n=200))), ("MA250 tạm dừng", ("ma", "tam_dung", dict(n=250))),
         ("MA200 có bán 50%", ("ma", "ban_mua", dict(n=200))), ("Độ rộng<40% tạm dừng", ("do_rong", "tam_dung", dict(nguong=0.40))),
         ("Độ rộng<30% tạm dừng", ("do_rong", "tam_dung", dict(nguong=0.30))), ("Biến động>1,5 lần tạm dừng", ("bien_dong", "tam_dung", dict(he_so=1.5))),
         ("Dừng khi cả MA200 và độ rộng xấu", ("ma_va_do_rong", "tam_dung", {})), ("Dừng khi một trong hai xấu", ("ma_hoac_do_rong", "tam_dung", {}))]
def chay_rule(e, ten, spec): return e.chay(ten, LoiChiBao(spec[0], spec[1], **spec[2]))
# 1) toàn kỳ 2015→nay và hai đoạn
for tu, den in (("2015-01-01", None), ("2015-01-01", "2020-12-31"), ("2021-01-01", None)):
    e = Engine(gia, tu=tu, den=den); chuan = e.chay("Mua đều E1VFVN30", MuaDeuETF()); ks = [chuan] + [chay_rule(e, t, sp) for t, sp in RULES]
    print(f"\n### {tu} → {den or 'nay'}\n"); print(in_bang([chi_so(k) for k in ks]))
    if den is None and tu == "2015-01-01":
        for k in ks[1:]: r = bootstrap_chu_dong(k, chuan); print(f"  {k.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.1f}, {r['ci95_cao_%']:+.1f}], p(≤0)={r['p_mot_phia(chu_dong<=0)']:.2f}")
# 2) walk-forward cuốn chiếu: huấn luyện 5 năm chọn luật theo CAGR; đánh giá giai đoạn sau
print("\n### Walk-forward (chọn luật có CAGR cao nhất ở đoạn huấn luyện, đánh giá đoạn sau)")
rows = []
for (a, b, c, d) in (("2015-01-01", "2019-12-31", "2020-01-01", "2021-12-31"), ("2017-01-01", "2021-12-31", "2022-01-01", "2023-12-31"), ("2019-01-01", "2023-12-31", "2024-01-01", None)):
    et = Engine(gia, tu=a, den=b); kt = {t: chi_so(chay_rule(et, t, sp))["CAGR (XIRR)"] for t, sp in RULES}
    chon = max(kt, key=kt.get); spec = dict(RULES)[chon]
    ee = Engine(gia, tu=c, den=d); k = chay_rule(ee, chon, spec); ch = ee.chay("E1", MuaDeuETF()); ci, cc = chi_so(k), chi_so(ch)
    rows.append({"Huấn luyện": f"{a[:4]}–{b[:4]}", "Luật chọn": chon, "CAGR huấn luyện": f"{kt[chon]*100:.2f}%", "Kiểm tra": f"{c[:4]}–{(d or 'nay')[:4]}", "CAGR luật": f"{ci['CAGR (XIRR)']*100:.2f}%", "CAGR E1VFVN30": f"{cc['CAGR (XIRR)']*100:.2f}%", "MDD luật": f"{ci['MDD']*100:.1f}%", "MDD E1VFVN30": f"{cc['MDD']*100:.1f}%"})
print(pd.DataFrame(rows).to_markdown(index=False))
