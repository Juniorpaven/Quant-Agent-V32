"""Báo cáo hằng ngày V34: luật thị trường (tầng 3), lõi E1VFVN30, danh sách chất lượng (tầng 2, chỉ theo dõi), vị thế và tiền mặt.
Mọi bảng và số liệu do code tạo; Gemini (nếu có khóa) chỉ viết lời bình từ số liệu đã tính, không tìm kiếm web, không điền số.
Chỉ gửi vào ngày có phiên giao dịch (dữ liệu VNINDEX có thanh ngày hôm nay). Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư.
Người nhận lấy từ biến môi trường EMAIL_NHAN (nhiều địa chỉ cách nhau bằng dấu phẩy); nếu không đặt thì gửi cho EMAIL_USER."""
import json, os, sys, time, smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import numpy as np, pandas as pd, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tang2_chon_ma import DuLieuCoBan, loc, diem_nhan_to, CHUA_DANH_GIA

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GIA = os.path.join(GOC, "data", "gia")
MA_LOI = "E1VFVN30"
MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash"]


def hom_nay_vn():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).date()


def doc_gia(ma):
    f = os.path.join(GIA, f"{ma}.csv")
    return pd.read_csv(f, parse_dates=["Date"]).set_index("Date") if os.path.exists(f) else None


def cap_nhat_gia(ma, so_ngay=40):
    """Tải thêm các thanh ngày gần đây từ Entrade rồi gộp vào CSV. Lỗi mạng thì dùng dữ liệu đã lưu."""
    df = doc_gia(ma)
    if df is None: return None
    loai = "index" if ma in ("VNINDEX", "VN30") else "stock"
    t1 = int(time.time()); t0 = t1 - 86400 * so_ngay
    try:
        d = requests.get(f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{loai}?from={t0}&to={t1}&symbol={ma}&resolution=1D",
                         headers={"User-Agent": "quant-agent-research/1.0"}, timeout=15).json()
        if d.get("c"):
            moi = pd.DataFrame({"Date": pd.to_datetime(d["t"], unit="s").normalize(), "Open": d["o"], "High": d["h"], "Low": d["l"], "Close": d["c"], "Volume": d["v"]})
            moi = moi[(moi.Close > 0) & (moi.Volume >= 0)].set_index("Date")
            df = pd.concat([df, moi]); df = df[~df.index.duplicated(keep="last")].sort_index()
            df.reset_index().to_csv(os.path.join(GIA, f"{ma}.csv"), index=False)
    except Exception as e:
        print(f"⚠️ Không cập nhật được giá {ma}: {type(e).__name__}")
    return df


def tai_vi_the():
    f = os.path.join(GOC, "data", "vi_the.json")
    if not os.path.exists(f): return None
    try: return json.load(open(f))
    except Exception: return None


def lap_bao_cao(cap_nhat=True):
    dl = DuLieuCoBan(os.path.join(GOC, "data", "bctc"))
    ds = [m for m in dl.nam if os.path.exists(os.path.join(GIA, f"{m}.csv"))]
    gia = {}
    for m in ["VNINDEX", MA_LOI] + ds:
        g = cap_nhat_gia(m) if cap_nhat else doc_gia(m)
        if g is not None and len(g): gia[m] = g
    vn = gia["VNINDEX"].Close
    ngay_cuoi = vn.index[-1].date()
    sl = {"ngay_du_lieu": str(ngay_cuoi), "hom_nay": str(hom_nay_vn())}
    ma200 = vn.rolling(200).mean()
    sl.update(vnindex=round(float(vn.iloc[-1]), 2), ma200=round(float(ma200.iloc[-1]), 2), tren_ma200=bool(vn.iloc[-1] > ma200.iloc[-1]),
              cach_ma200_pct=round(float(vn.iloc[-1] / ma200.iloc[-1] - 1) * 100, 2))
    d = pd.Timestamp(ngay_cuoi)
    dat = [m for m in ds if m in gia and loc(dl, m, d)[0] and (gia[m].Close * gia[m].Volume * 1000).tail(20).mean() >= 10e9]
    close = pd.DataFrame({m: gia[m].Close for m in dat}).reindex(vn.index) if dat else None
    bang = diem_nhan_to(dl, close, None, dat, d, len(vn) - 1) if dat else pd.DataFrame()
    top = bang.head(12)
    sl["danh_sach_chat_luong"] = [{"ma": m, "diem": round(float(top.loc[m, "diem"]), 2), "roe_tb": round(float(top.loc[m, "roe"]) * 100, 1),
                                   "chua_danh_gia": sum(1 for v in loc(dl, m, d)[1].values() if v == CHUA_DANH_GIA)} for m in top.index]
    sl["so_ma_dat_loc"] = len(dat)
    vt = tai_vi_the()
    if vt:
        dong, tong_cp = [], 0.0
        for m, sluong in vt.get("co_phieu", {}).items():
            g = gia[m].Close.iloc[-1] * 1000 if m in gia else np.nan
            gt = sluong * g if np.isfinite(g) else np.nan
            dong.append({"ma": m, "so_luong": sluong, "gia": round(float(g) / 1000, 2) if np.isfinite(g) else None, "gia_tri": gt})
            tong_cp += gt if np.isfinite(gt) else 0
        tm = float(vt.get("tien_mat", 0)); tong = tong_cp + tm
        sl.update(vi_the=dong, tien_mat=tm, ty_le_tien_mat_pct=round(tm / tong * 100, 1) if tong > 0 else None)
    else:
        sl["vi_the"] = None
    return sl


def huong_dan(sl):
    if sl["tren_ma200"]:
        return "Giải ngân lõi như bình thường: mua đều E1VFVN30 theo lịch tháng."
    return "VN-Index dưới MA200: tạm dừng mua thêm lõi (giữ tiền mặt), không bán. Mua lại khi VN-Index vượt MA200."


def dung_markdown(sl, loi_binh):
    d = [f"# Báo cáo Quant V34 – dữ liệu phiên {sl['ngay_du_lieu']}", "",
         "## 1. Luật thị trường (tầng 3)", "",
         f"- VN-Index: **{sl['vnindex']}**, MA200: **{sl['ma200']}** ({sl['cach_ma200_pct']:+.2f}%).",
         f"- Hướng dẫn: **{huong_dan(sl)}**", "", "## 2. Vị thế và tiền mặt", ""]
    if sl.get("vi_the"):
        d += ["| Mã | Số lượng | Giá (nghìn đồng) | Giá trị (đồng) |", "| --- | ---: | ---: | ---: |"]
        d += [f"| {r['ma']} | {r['so_luong']:,} | {r['gia']} | {r['gia_tri']:,.0f} |" for r in sl["vi_the"]]
        d += ["", f"- Tiền mặt: {sl['tien_mat']:,.0f} đồng; tỷ lệ tiền mặt: **{sl['ty_le_tien_mat_pct']}%**."]
    else:
        d.append("Chưa có `data/vi_the.json` nên không có số liệu vị thế (không có dữ liệu).")
    d += ["", "## 3. Danh sách chất lượng (chỉ theo dõi)", "",
          f"Có {sl['so_ma_dat_loc']} mã qua các phép thử tự động. Backtest 2021–2026 cho thấy lõi chọn mã **chưa thắng** mua đều E1VFVN30, nên đây không phải khuyến nghị mua. Phép thử 4, 5, 7 (bên liên quan, kiểm toán, người nội bộ) chưa có dữ liệu tự động.", ""]
    if sl["danh_sach_chat_luong"]:
        d += ["| Mã | Điểm nhân tố | ROE bình quân (%) | Số phép thử chưa đánh giá được |", "| --- | ---: | ---: | ---: |"]
        d += [f"| {r['ma']} | {r['diem']} | {r['roe_tb']} | {r['chua_danh_gia']} |" for r in sl["danh_sach_chat_luong"]]
    d += ["", "## 4. Lời bình", "", loi_binh or "Không có lời bình (không có khóa Gemini hoặc lỗi gọi mô hình).", "",
          "_Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư._"]
    return "\n".join(d)


def viet_loi_binh(sl):
    key = os.environ.get("GEMINI_API_KEY")
    if not key: return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
    except Exception:
        return None
    tom_tat = {k: sl[k] for k in ("ngay_du_lieu", "vnindex", "ma200", "tren_ma200", "cach_ma200_pct", "so_ma_dat_loc", "ty_le_tien_mat_pct") if k in sl}
    prompt = ("Viết lời bình ngắn (tối đa 120 từ, tiếng Việt có dấu) cho báo cáo đầu tư dài hạn. CHỈ dùng các số liệu trong JSON sau; "
              "không tìm kiếm, không thêm số liệu hay tin tức nào khác; trường nào thiếu thì ghi 'không có dữ liệu'. Không khuyến nghị mua bán cụ thể.\n" + json.dumps(tom_tat, ensure_ascii=False))
    for m in MODELS:
        try: return genai.GenerativeModel(m).generate_content(prompt).text
        except Exception as e: print(f"⚠️ Gemini {m}: {type(e).__name__}")
    return None


def gui_mail(tieu_de, noi_dung):
    user, pw = os.environ.get("EMAIL_USER", ""), os.environ.get("EMAIL_PASS", "")
    nhan = [x.strip() for x in (os.environ.get("EMAIL_NHAN") or user).split(",") if x.strip()]
    if not user or not pw or not nhan:
        print("⚠️ Bỏ qua gửi Email vì chưa cấu hình tài khoản."); return
    import markdown
    html = markdown.markdown(noi_dung, extensions=["tables"])
    msg = MIMEMultipart("alternative"); msg["From"], msg["To"], msg["Subject"] = user, ", ".join(nhan), tieu_de
    msg.attach(MIMEText(noi_dung, "plain")); msg.attach(MIMEText(f"<html><body style='font-family:Segoe UI,Arial,sans-serif'>{html}</body></html>", "html"))
    try:
        s = smtplib.SMTP("smtp.gmail.com", 587); s.starttls(); s.login(user, pw); s.send_message(msg); s.quit()
        print(f"📧 Đã gửi báo cáo V34 đến {len(nhan)} địa chỉ.")
    except Exception as e:
        print(f"❌ Lỗi gửi Email: {e}")


if __name__ == "__main__":
    khong_gui, khong_mang = "--khong-gui" in sys.argv, "--khong-mang" in sys.argv
    sl = lap_bao_cao(cap_nhat=not khong_mang)
    if sl["ngay_du_lieu"] != sl["hom_nay"] and "--bo-qua-kiem-tra-phien" not in sys.argv:
        print(f"Hôm nay {sl['hom_nay']} không có phiên giao dịch (dữ liệu mới nhất {sl['ngay_du_lieu']}). Không gửi báo cáo."); sys.exit(0)
    bc = dung_markdown(sl, viet_loi_binh(sl))
    print(bc)
    if not khong_gui: gui_mail(f"Quant V34 – {sl['ngay_du_lieu']}", bc)
