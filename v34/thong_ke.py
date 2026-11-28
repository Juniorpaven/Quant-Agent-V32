"""Kiểm định thống kê cho so sánh với chuẩn: bootstrap theo khối trên lợi suất tháng chủ động (TWR)."""
import numpy as np, pandas as pd


def loi_suat_thang(kq):
    nav, dg = kq.nav, kq.dong_gop
    ret = ((nav - dg) / nav.shift(1) - 1).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return (1 + ret).groupby([ret.index.year, ret.index.month]).prod() - 1


def bootstrap_chu_dong(kq, chuan, khoi=3, n=5000, seed=1):
    a, b = loi_suat_thang(kq), loi_suat_thang(chuan)
    x = (a - b).dropna().values; T = len(x)
    rng = np.random.default_rng(seed)
    trung_binh = []
    for _ in range(n):
        so_khoi = int(np.ceil(T / khoi)); st = rng.integers(0, T, so_khoi)
        mau = np.concatenate([x[(s + np.arange(khoi)) % T] for s in st])[:T]
        trung_binh.append(mau.mean())
    tb = np.array(trung_binh)
    return {"so_thang": T, "chu_dong_nam_%": ((1 + x.mean()) ** 12 - 1) * 100,
            "ci95_thap_%": ((1 + np.percentile(tb, 2.5)) ** 12 - 1) * 100, "ci95_cao_%": ((1 + np.percentile(tb, 97.5)) ** 12 - 1) * 100,
            "p_mot_phia(chu_dong<=0)": float((tb <= 0).mean()), "p_mot_phia(chu_dong>=0)": float((tb >= 0).mean()),
            "IR_nam": float(x.mean() / x.std() * np.sqrt(12)) if x.std() > 0 else np.nan}
