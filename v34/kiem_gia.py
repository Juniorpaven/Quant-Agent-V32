"""Kiểm tra nhất quán giá: so giá đóng cửa Entrade (đã lưu trong data/gia) với giá điều chỉnh và giá thô của Vietcap IQ cho một số mã mẫu."""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_mo_rong as mr, tai_du_lieu as td
os.makedirs("data/kiem_gia", exist_ok=True)
for ma in "FPT VCB HPG VNM MWG REE SSI HDB DGC PNJ PVD GAS ACB MBB".split():
    ds = mr.trang(f"{mr.IQ}/{ma}/price-history")
    if not ds: print("thiếu", ma, flush=True); continue
    df = pd.DataFrame(ds)
    out = pd.DataFrame({"Date": pd.to_datetime(df["tradingDate"]).dt.normalize(), "dong_tho": df["closePrice"] / 1000, "dieu_chinh": df["closePriceAdjusted"] / 1000})
    out.drop_duplicates("Date").sort_values("Date").to_csv(f"data/kiem_gia/{ma}.csv", index=False)
    print(ma, len(out), flush=True)
