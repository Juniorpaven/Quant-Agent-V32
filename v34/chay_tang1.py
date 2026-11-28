"""Tầng 1: khung lõi/vệ tinh xấp xỉ bằng hai túi vốn độc lập (không cân bằng lại giữa hai túi), chia nạp hằng tháng 75%/25%."""
import sys; sys.path.insert(0, "v34")
import pandas as pd
from khung_backtest import *
from loi_tang2 import *
from tang4_wyckoff import VeTinhWyckoff
gia = nap_gia("data/gia"); dl = DuLieuCoBan(); ds = [m for m in dl.nam if m in gia]
def ghep(ten, a, b):
    return KetQua(ten, a.nav.add(b.nav, fill_value=0), a.dong_gop.add(b.dong_gop, fill_value=0), a.chi_phi + b.chi_phi, a.giao_dich_ban + b.giao_dich_ban, a.so_lenh_bi_chan + b.so_lenh_bi_chan)
def chay(tu, den):
    e75, e25, e100 = (Engine(gia, tu=tu, den=den, nap_hang_thang=x) for x in (7.5e6, 2.5e6, 10e6))
    chuan = e100.chay("Mua đều E1VFVN30", MuaDeuETF())
    loi_t2 = e75.chay("lõi T2", LoiTang2(dl, 12, ds_ma=ds)); loi_etf = e75.chay("lõi ETF", MuaDeuETF())
    vt = e25.chay("vệ tinh", VeTinhWyckoff(dl, gia, ds)); vt_etf = e25.chay("vệ tinh ETF", MuaDeuETF())
    return [chuan, ghep("Tầng 1: 75% lõi T2 + 25% vệ tinh Wyckoff", loi_t2, vt), ghep("75% lõi E1VFVN30 + 25% vệ tinh Wyckoff", loi_etf, vt),
            ghep("75% lõi T2 + 25% E1VFVN30", loi_t2, vt_etf)]
if __name__ == "__main__":
    for tu, den in (("2021-05-01", None), ("2021-05-01", "2023-12-31"), ("2024-01-01", None)):
        print(f"\n### {tu} → {den or 'nay'}\n"); print(in_bang([chi_so(k) for k in chay(tu, den)]))
