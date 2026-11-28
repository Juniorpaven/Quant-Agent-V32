"""Tầng 4 mở rộng: toàn bộ tập mã, từ 2015 (tín hiệu chỉ cần giá), kèm biến thể và độ nhạy tham số. Có và không có bộ lọc chất lượng cho đoạn 2021→nay."""
import sys; sys.path.insert(0, "v34")
from khung_backtest import *
from tang2_chon_ma import DuLieuCoBan
from tang4_wyckoff import *
from thong_ke import bootstrap_chu_dong
gia = nap_gia("data/gia"); dl = DuLieuCoBan(); ds = [m for m in gia if m not in ("VNINDEX", "VN30", "E1VFVN30")]
cache = {}
def chay(tu, den, cau_hinh, loc_ct=False):
    e = Engine(gia, tu=tu, den=den); chuan = e.chay("Mua đều E1VFVN30", MuaDeuETF()); kqs = [chuan]; dem = []
    for ten, kw_t, kw_s in cau_hinh:
        st = VeTinhWyckoff(dl, gia, ds, chi_ma_dat_loc=loc_ct, tin_hieu_kw=kw_t, cache=cache, **kw_s); k = e.chay(ten, st); kqs.append(k); dem.append(sum(1 for x in st.nhat_ky if x[1].startswith("vào")))
    return chuan, kqs, dem
CH = [("Cơ sở (Spring+Test hoặc SOS)", {}, {}), ("Chỉ SOS", {"che_do": "chi_sos"}, {}), ("Chỉ Spring+Test", {"che_do": "chi_spring"}, {}),
      ("Vùng ≥ 6 tuần", {"san_tuan": 6}, {}), ("Vùng ≥ 12 tuần", {"san_tuan": 12}, {}), ("Biên độ vùng ≤ 20%", {"bien_do": 0.20}, {}), ("Biên độ vùng ≤ 40%", {"bien_do": 0.40}, {}),
      ("SOS khối lượng ≥ 2,0 lần", {"sos_vr": 2.0}, {}), ("Dừng lỗ 1,5 ATR / bám 2 ATR", {}, {"he_so_dung": 1.5, "he_so_bam": 2.0}), ("Dừng lỗ 3 ATR / bám 4 ATR", {}, {"he_so_dung": 3.0, "he_so_bam": 4.0})]
for tu, den, loc_ct in (("2015-01-01", None, False), ("2015-01-01", "2020-12-31", False), ("2021-01-01", None, False), ("2021-05-01", None, True)):
    chuan, kqs, dem = chay(tu, den, CH, loc_ct)
    print(f"\n### {tu} → {den or 'nay'} (lọc chất lượng: {loc_ct}); số lệnh vào: {dem}\n"); print(in_bang([chi_so(k) for k in kqs]))
    if tu == "2015-01-01" and den is None:
        for k in kqs[1:4]: r = bootstrap_chu_dong(k, chuan); print(f"  bootstrap {k.ten}: chủ động {r['chu_dong_nam_%']:+.2f}%/năm, CI95 [{r['ci95_thap_%']:+.2f}, {r['ci95_cao_%']:+.2f}], p(≤0)={r['p_mot_phia(chu_dong<=0)']:.2f}")
