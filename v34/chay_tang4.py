import sys; sys.path.insert(0, "v34")
from khung_backtest import *
from tang2_chon_ma import DuLieuCoBan
from tang4_wyckoff import *
gia = nap_gia("data/gia"); dl = DuLieuCoBan(); ds = [m for m in dl.nam if m in gia]
def chay(tu, den):
    e = Engine(gia, tu=tu, den=den)
    ks = [e.chay("Mua đều E1VFVN30", MuaDeuETF())]
    for ten, kw in (("Vệ tinh Wyckoff (mã đạt lọc)", {}), ("Vệ tinh Wyckoff (mọi mã, không lọc)", {"chi_ma_dat_loc": False})):
        st = VeTinhWyckoff(dl, gia, ds, **kw); k = e.chay(ten, st); ks.append(k); k.so_lenh = sum(1 for x in st.nhat_ky if x[1].startswith("vào"))
    return ks
if __name__ == "__main__":
    for tu, den in (("2021-05-01", None), ("2021-05-01", "2023-12-31"), ("2024-01-01", None)):
        ks = chay(tu, den); print(f"\n### {tu} → {den or 'nay'}  (số lệnh vào: {[getattr(k,'so_lenh',0) for k in ks]})\n"); print(in_bang([chi_so(k) for k in ks]))
