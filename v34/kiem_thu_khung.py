"""Kiểm thử khung backtest bằng dữ liệu giả lập (không phải kết quả thật)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "v34")
from khung_backtest import *
rng = np.random.default_rng(1)
ng = pd.bdate_range("2015-01-01", "2024-12-31")
def mk(mu, sd, p0):
    c = p0 * np.exp(np.cumsum(rng.normal(mu, sd, len(ng))))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, .003, len(ng)))
    return pd.DataFrame({"Open": o, "High": np.maximum(o, c), "Low": np.minimum(o, c), "Close": c, "Volume": rng.integers(2e6, 5e6, len(ng))}, index=ng)
gia = {"VNINDEX": mk(.0003, .01, 600), "E1VFVN30": mk(.0003, .01, 10), "AAA": mk(.0005, .018, 30)}
e = Engine(gia, tu="2015-01-01")
a = e.chay("ETF", MuaDeuETF()); print(in_bang([chi_so(a), chi_so(chi_so_chi_so(gia, "VNINDEX", "2015-01-01"))]) if False else chi_so(a))
print("nav cuối", a.nav.iloc[-1] / 1e6, "nạp", a.dong_gop.sum() / 1e6)
