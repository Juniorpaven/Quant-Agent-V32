import sys; sys.path.insert(0, "v34")
import pandas as pd
from khung_backtest import *
from loi_tang2 import *
from loi_chung import *
from thong_ke import *
from tang4_wyckoff import VeTinhWyckoff
from tang3_luat_thi_truong import LoiMA200
gia = nap_gia("data/gia"); dl = DuLieuCoBan(); ds = [m for m in dl.nam if m in gia]
bang = []
def so(ten, kq, chuan):
    r = bootstrap_chu_dong(kq, chuan); r["Tên"] = ten; bang.append(r); return r
# --- 2021-05 → nay
e = Engine(gia, tu="2021-05-01"); chuan = e.chay("E1VFVN30", MuaDeuETF())
rong = [m for m in gia if m not in ("VNINDEX", "VN30", "E1VFVN30")]
top30 = e.chay("Rổ đều top 30 thanh khoản (không lọc)", LoiDanhSach(chon_top_thanh_khoan(rong, 30), 30))
t2 = e.chay("T2 N=12", LoiTang2(dl, 12, ds_ma=ds))
t2b = e.chay("T2 trần NH 4 + pha 50% ETF", LoiTang2(dl, 12, ds_ma=ds, max_ngan_hang=4, ty_le_loi=0.5))
w = e.chay("Vệ tinh Wyckoff (mã đạt lọc)", VeTinhWyckoff(dl, gia, ds))
print("== 2021-05 → nay"); print(in_bang([chi_so(k) for k in (chuan, top30, t2, t2b, w)]))
for ten, k in (("Rổ top 30 thanh khoản so với E1VFVN30", top30), ("T2 N=12 so với E1VFVN30", t2), ("T2 trần NH 4 + pha 50% so với E1VFVN30", t2b), ("Wyckoff so với E1VFVN30", w)): so(ten, k, chuan)
so("T2 N=12 so với rổ top 30 thanh khoản", t2, top30)
# --- 2015 → nay (tầng 3)
e15 = Engine(gia, tu="2015-01-01"); c15 = e15.chay("E1VFVN30", MuaDeuETF())
for ten, kw in (("MA200 tạm dừng so với E1VFVN30 (2015→)", ("tam_dung",)), ("MA200 có bán so với E1VFVN30 (2015→)", ("ban_mua",))): so(ten, e15.chay(ten, LoiMA200(200, 0.5, kw[0])), c15)
df = pd.DataFrame(bang).set_index("Tên")
print("\n== Bootstrap theo khối (3 tháng), 5000 lần, lợi suất tháng chủ động so với chuẩn")
print(df.round(2).to_markdown())
n_thu = 35; print(f"\nHiệu chỉnh nhiều lần thử: ~{n_thu} cấu hình đã thử, ngưỡng Bonferroni p < {0.05/n_thu:.4f}")
# --- trượt giá
print("\n== Kịch bản trượt giá (2021-05 → nay)")
ks = []
for tg in (0.0, 0.002, 0.005):
    ex = Engine(gia, tu="2021-05-01", truot_gia=tg)
    ks += [chi_so(ex.chay(f"E1VFVN30 trượt {tg*100:.1f}%", MuaDeuETF())), chi_so(ex.chay(f"T2 N=12 trượt {tg*100:.1f}%", LoiTang2(dl, 12, ds_ma=ds))), chi_so(ex.chay(f"Wyckoff trượt {tg*100:.1f}%", VeTinhWyckoff(dl, gia, ds)))]
print(in_bang(ks))
