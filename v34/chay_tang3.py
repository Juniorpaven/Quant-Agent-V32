import sys; sys.path.insert(0, "v34")
from khung_backtest import *
from tang3_luat_thi_truong import LoiMA200
gia = nap_gia("data/gia")
def chay(tu, den, nap=10e6):
    e = Engine(gia, tu=tu, den=den, nap_hang_thang=nap)
    ds = [chi_so(e.chay("Mua đều E1VFVN30", MuaDeuETF())), chi_so(chi_so_chi_so(gia, "VNINDEX", tu, den, nap))]
    for n in (150, 200, 250):
        for cd, r in (("ban_mua", 0.5), ("tam_dung", 0.5)):
            ds.append(chi_so(e.chay(f"MA{n} {cd} {int(r*100)}%", LoiMA200(n, r, cd))))
    return in_bang(ds)
for tu, den in (("2015-01-01", None), ("2015-01-01", "2020-12-31"), ("2021-01-01", None)):
    print(f"\n### {tu} → {den or 'nay'}\n"); print(chay(tu, den))
