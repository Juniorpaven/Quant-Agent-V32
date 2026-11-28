import sys; sys.path.insert(0, "v34")
import numpy as np
from khung_backtest import *
from loi_tang2 import *
gia = nap_gia("data/gia"); dl = DuLieuCoBan(); ds = [m for m in dl.nam if m in gia]
e = Engine(gia, tu="2021-05-01")
ds_kq = [chi_so(e.chay("Mua đều E1VFVN30", MuaDeuETF()))]
for ten, kw in (("Xếp hạng điểm tổng hợp N=12", {}), ("Chỉ ROE N=12", {"xep": "roe"}), ("Chỉ giá trị N=12", {"xep": "gia_tri"}), ("Chỉ động lượng N=12", {"xep": "mom"}),
                ("Tất cả mã đạt lọc (N=30, đều)", {"n": 30})):
    n = kw.pop("n", 12); ds_kq.append(chi_so(e.chay(ten, LoiTang2(dl, n, ds_ma=ds, **kw))))
ng = []
for sd in range(8):
    k = chi_so(e.chay(f"ngẫu nhiên {sd}", LoiTang2(dl, 12, ds_ma=ds, xep="ngau_nhien", seed=sd))); ng.append((k["CAGR (XIRR)"], k["MDD"]))
print(in_bang(ds_kq))
a = np.array(ng); print(f"\nNgẫu nhiên trong mã đạt lọc (8 lần, N=12): CAGR trung bình {a[:,0].mean()*100:.2f}% (min {a[:,0].min()*100:.2f}%, max {a[:,0].max()*100:.2f}%), MDD trung bình {a[:,1].mean()*100:.2f}%")
