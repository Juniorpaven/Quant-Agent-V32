"""Tải giá điều chỉnh toàn lịch sử (từ 2006) từ Vietcap IQ cho mọi mã có BCTC, ghi vào data/gia_dai/ (cột như data/gia)."""
import glob, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_du_lieu as td, tai_mo_rong as mr
os.makedirs("data/gia_dai", exist_ok=True)
loi = []
for f in sorted(glob.glob("data/bctc/[A-Z]*.json")):
    ma = os.path.basename(f)[:-5]
    if os.path.exists(f"data/gia_dai/{ma}.csv"): continue
    df = mr.tai_gia_iq(ma)
    if df is None: loi.append(ma); print("thiếu", ma, flush=True); continue
    df.to_csv(f"data/gia_dai/{ma}.csv", index=False); print("gia_dai", ma, len(df), df.Date.min().date(), flush=True)
print("LỖI", loi)
