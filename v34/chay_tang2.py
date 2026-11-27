import sys; sys.path.insert(0, "v34")
from khung_backtest import *
from loi_tang2 import *
gia = nap_gia("data/gia"); dl = DuLieuCoBan()
ds = [m for m in dl.nam if m in gia]
chi = []
def chay(tu, den):
    e = Engine(gia, tu=tu, den=den)
    kqs = [e.chay("Mua đều E1VFVN30", MuaDeuETF()), e.chay("T2 N=12", LoiTang2(dl, 12, ds_ma=ds)),
           e.chay("T2 N=12 + tạm dừng MA200", LoiTang2(dl, 12, chan_ma200=True, ds_ma=ds)),
           e.chay("T2 N=12 trần NH 4", LoiTang2(dl, 12, ds_ma=ds, max_ngan_hang=4)),
           e.chay("T2 N=15", LoiTang2(dl, 15, ds_ma=ds)),
           e.chay("T2 N=12 pha 50% ETF", LoiTang2(dl, 12, ds_ma=ds, ty_le_loi=0.5)),
           e.chay("T2 N=12 trần NH 4 + pha 50% ETF", LoiTang2(dl, 12, ds_ma=ds, max_ngan_hang=4, ty_le_loi=0.5))]
    return kqs
if __name__ == "__main__":
    for tu, den in (("2021-05-01", None), ("2021-05-01", "2023-12-31"), ("2024-01-01", None)):
        kqs = chay(tu, den); print(f"\n### {tu} → {den or 'nay'}\n"); print(in_bang([chi_so(k) for k in kqs]))
        if den is None and tu == "2021-05-01":
            for d, giu, thoat in kqs[1].nhat_ky and []: pass
