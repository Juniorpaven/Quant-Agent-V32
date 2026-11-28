"""Báo cáo hằng ngày V34: đủ các tầng (luật thị trường, lõi/phân bổ, danh sách chất lượng, trạng thái hệ thống), dữ liệu BCTC mới, và phần thay đổi so với lần trước.
Mọi bảng và số liệu do code tạo; Gemini (nếu có khóa) chỉ viết lời bình từ số liệu đã tính, không tìm kiếm web, không điền số.
Chỉ gửi vào ngày có phiên giao dịch (dữ liệu VNINDEX có thanh ngày hôm nay). Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư.
Người nhận lấy từ biến môi trường EMAIL_NHAN (nhiều địa chỉ cách nhau bằng dấu phẩy); nếu không đặt thì gửi cho EMAIL_USER.
Giá được tải trực tiếp từ Entrade (430 ngày) cho các mã thanh khoản nên không phải lưu giá mỗi ngày; không có mạng thì dùng dữ liệu đã lưu."""
import glob, json, os, sys, time, smtplib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import numpy as np, pandas as pd, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tang2_chon_ma import diem_nhan_to, CHUA_DANH_GIA
from tang2_ttm import DuLieuTTM, loc_ttm

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(GOC, "data")
MA_LOI = "E1VFVN30"
MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash"]
NGUONG_TK_TUYEN = 3e9       # lọc sơ bộ theo giá trị giao dịch dữ liệu đã lưu (đồng/phiên)
NGUONG_TK_LOC = 10e9        # ngưỡng thanh khoản của danh sách chất lượng (đồng/phiên, 20 phiên)
FILE_TRANG_THAI = os.path.join(DATA, "_trang_thai_bao_cao.json")
FILE_TRANG = os.path.join(GOC, "docs", "BAO_CAO_MOI_NHAT.md")


def hom_nay_vn():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).date()


# ---------------------------------------------------------------- dữ liệu giá
def doc_gia_luu(ma):
    for f in (os.path.join(DATA, "gia_dai", f"{ma}.csv.gz"), os.path.join(DATA, "gia_dai", f"{ma}.csv"), os.path.join(DATA, "gia", f"{ma}.csv")):
        if os.path.exists(f):
            return pd.read_csv(f, parse_dates=["Date"]).drop_duplicates("Date").set_index("Date").sort_index()
    return None


def tai_gia_entrade(ma, so_ngay=430):
    """Giá ngày gần đây từ Entrade; None nếu lỗi (dùng dữ liệu đã lưu)."""
    loai = "index" if ma in ("VNINDEX", "VN30") else "stock"
    t1 = int(time.time()); t0 = t1 - 86400 * so_ngay
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{loai}?from={t0}&to={t1}&symbol={ma}&resolution=1D"
    for lan in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": "quant-agent-research/1.0"}, timeout=20)
            if r.status_code == 429: time.sleep(2); continue
            d = r.json()
            if d.get("c"):
                df = pd.DataFrame({"Date": pd.to_datetime(d["t"], unit="s").normalize(), "Open": d["o"], "High": d["h"], "Low": d["l"], "Close": d["c"], "Volume": d["v"]})
                df = df[(df.Close > 0) & (df.Volume >= 0)].drop_duplicates("Date").set_index("Date").sort_index()
                return df if len(df) else None
            return None
        except Exception:
            time.sleep(1)
    return None


def chon_ma_theo_doi(dl):
    """Mã đang niêm yết (HSX, HNX) có BCTC và giá lưu, thanh khoản sơ bộ đủ lớn."""
    f = os.path.join(DATA, "ds_ma.json")
    san = {x["ma"]: x["san"] for x in json.load(open(f))} if os.path.exists(f) else {}
    ket = []
    for m in dl.nam:
        if san and san.get(m) not in ("HSX", "HNX"): continue
        g = doc_gia_luu(m)
        if g is None or len(g) < 250: continue
        if (g.Close * g.Volume * 1000).tail(20).mean() >= NGUONG_TK_TUYEN: ket.append(m)
    return sorted(ket)


def tai_gia_tat_ca(ds, cap_nhat):
    """Trả về (gia, so_moi, so_cu): giá mới từ Entrade (song song) hoặc dữ liệu đã lưu khi lỗi/không mạng."""
    gia, moi = {}, 0
    cac = ["VNINDEX", MA_LOI] + ds
    tai = {}
    if cap_nhat:
        with ThreadPoolExecutor(8) as ex: tai = dict(zip(cac, ex.map(tai_gia_entrade, cac)))
    for m in cac:
        g = tai.get(m)
        if g is not None and len(g) > 100: gia[m] = g; moi += 1
        else:
            g = doc_gia_luu(m)
            if g is not None and len(g): gia[m] = g
    return gia, moi, len(gia) - moi


# ---------------------------------------------------------------- chỉ báo tầng 3
def chi_bao_tang3(gia, ds_thanh_khoan):
    """VN-Index so với MA200 (luật) và các chỉ báo tham khảo: độ rộng, biến động, độ sâu so với đỉnh 52 tuần, số phiên liên tiếp cùng phía MA200."""
    vn = gia["VNINDEX"].Close
    ma200 = vn.rolling(200).mean()
    tren = (vn > ma200).dropna()
    chuoi = 1
    for i in range(len(tren) - 2, -1, -1):
        if tren.iloc[i] == tren.iloc[-1]: chuoi += 1
        else: break
    out = dict(vnindex=round(float(vn.iloc[-1]), 2), ma200=round(float(ma200.iloc[-1]), 2), tren_ma200=bool(vn.iloc[-1] > ma200.iloc[-1]),
               cach_ma200_pct=round(float(vn.iloc[-1] / ma200.iloc[-1] - 1) * 100, 2), so_phien_cung_phia=int(chuoi))
    r = np.log(vn).diff(); v20 = r.rolling(20).std() * np.sqrt(250)
    med = v20.rolling(250, min_periods=120).median()
    out["bien_dong_20p_pct"] = round(float(v20.iloc[-1]) * 100, 1) if np.isfinite(v20.iloc[-1]) else None
    out["bien_dong_ty_le"] = round(float(v20.iloc[-1] / med.iloc[-1]), 2) if np.isfinite(med.iloc[-1]) and med.iloc[-1] > 0 else None
    out["cach_dinh_52t_pct"] = round(float(vn.iloc[-1] / vn.tail(250).max() - 1) * 100, 1)
    tren200 = tren50 = n = 0
    for m in ds_thanh_khoan:
        c = gia[m].Close if m in gia else None
        if c is None or len(c) < 210: continue
        n += 1; tren200 += bool(c.iloc[-1] > c.tail(200).mean()); tren50 += bool(c.iloc[-1] > c.tail(50).mean())
    out["do_rong_ma200_pct"] = round(100 * tren200 / n, 1) if n else None
    out["do_rong_ma50_pct"] = round(100 * tren50 / n, 1) if n else None
    out["do_rong_so_ma"] = n
    return out


# ---------------------------------------------------------------- tầng 2 và dữ liệu
def tai_nganh():
    out = {}
    for f in glob.glob(os.path.join(DATA, "ho_so", "[A-Z]*.json")):
        try: d = json.load(open(f)); out[d["ticker"]] = d.get("sectorVn") or d.get("sector") or ""
        except Exception: pass
    return out


def tai_vi_the():
    f = os.path.join(DATA, "vi_the.json")
    if not os.path.exists(f): return None
    try: return json.load(open(f))
    except Exception: return None


def lap_bao_cao(cap_nhat=True):
    dl = DuLieuTTM(os.path.join(DATA, "bctc"))
    ds = chon_ma_theo_doi(dl)
    gia, so_moi, so_cu = tai_gia_tat_ca(ds, cap_nhat)
    vn = gia["VNINDEX"].Close
    ngay_cuoi = vn.index[-1].date(); d = pd.Timestamp(ngay_cuoi)
    sl = {"ngay_du_lieu": str(ngay_cuoi), "hom_nay": str(hom_nay_vn()), "so_ma_theo_doi": len(ds), "gia_moi": so_moi, "gia_cu": so_cu}
    thanh_khoan = [m for m in ds if m in gia and (gia[m].Close * gia[m].Volume * 1000).tail(20).mean() >= NGUONG_TK_LOC]
    sl["tang3"] = chi_bao_tang3(gia, thanh_khoan)
    dat = [m for m in thanh_khoan if loc_ttm(dl, m, d)[0]]
    close = pd.DataFrame({m: gia[m].Close for m in dat}).reindex(vn.index) if dat else None
    bang = diem_nhan_to(dl, close, None, dat, d, len(vn) - 1, loc_fn=loc_ttm) if dat else pd.DataFrame()
    nganh = tai_nganh(); top = bang.head(12); dong = []
    for m in top.index:
        kq = loc_ttm(dl, m, d)[1]; ct = dl.co_tuc.get(m)
        so_nam_ct = int(ct[(ct.loai == "tien") & (ct.ngay <= d) & (ct.ngay > d - pd.Timedelta(days=365 * 5))].ngay.dt.year.nunique()) if ct is not None and len(ct) else None
        dong.append({"ma": m, "nganh": nganh.get(m, ""), "diem": round(float(top.loc[m, "diem"]), 2), "roe_tb": round(float(top.loc[m, "roe"]) * 100, 1), "co_tuc_tien_5nam": so_nam_ct,
                     "dat": sum(1 for v in kq.values() if v is True), "danh_gia": sum(1 for v in kq.values() if v != CHUA_DANH_GIA)})
    sl["danh_sach_chat_luong"], sl["tat_ca_dat_loc"], sl["so_ma_dat_loc"], sl["so_ma_thanh_khoan"] = dong, sorted(dat), len(dat), len(thanh_khoan)
    f_moi = os.path.join(DATA, "_bctc_moi.json")
    if os.path.exists(f_moi):
        try:
            j = json.load(open(f_moi)); han = d - pd.Timedelta(days=7)
            sl["bctc_moi_7_ngay"] = [x for x in j.get("lich_su", []) if pd.Timestamp(x["ngay"]) >= han]
            sl["bctc_cham"] = j.get("cham_cong_bo", []); sl["bctc_cap_nhat"] = j.get("cap_nhat")
        except Exception: pass
    vt = tai_vi_the()
    if vt:
        hang, tong_cp = [], 0.0
        for m, sluong in vt.get("co_phieu", {}).items():
            g = gia[m].Close.iloc[-1] * 1000 if m in gia else np.nan
            gt = sluong * g if np.isfinite(g) else np.nan
            hang.append({"ma": m, "so_luong": sluong, "gia": round(float(g) / 1000, 2) if np.isfinite(g) else None, "gia_tri": gt})
            tong_cp += gt if np.isfinite(gt) else 0
        tm = float(vt.get("tien_mat", 0)); tong = tong_cp + tm
        sl.update(vi_the=hang, tien_mat=tm, ty_le_tien_mat_pct=round(tm / tong * 100, 1) if tong > 0 else None)
    else:
        sl["vi_the"] = None
    return sl


# ---------------------------------------------------------------- thay đổi so với lần trước
def doc_trang_thai():
    try: return json.load(open(FILE_TRANG_THAI))
    except Exception: return None


def so_sanh_trang_thai(cu, sl):
    """Danh sách các thay đổi so với báo cáo trước. cu None (chưa có lần trước) thì trả về danh sách rỗng và cờ lần đầu."""
    if not cu: return [], True
    thay = []
    t3 = sl["tang3"]
    if cu.get("tren_ma200") is not None and cu["tren_ma200"] != t3["tren_ma200"]:
        thay.append(f"**Tín hiệu MA200 đổi:** từ {'trên' if cu['tren_ma200'] else 'dưới'} MA200 sang {'trên' if t3['tren_ma200'] else 'dưới'} MA200 → {huong_dan_ngan(t3)}")
    cu_loc, moi_loc = set(cu.get("tat_ca_dat_loc", [])), set(sl["tat_ca_dat_loc"])
    if moi_loc - cu_loc: thay.append("Mã **vào** danh sách đạt lọc chất lượng: " + ", ".join(sorted(moi_loc - cu_loc)))
    if cu_loc - moi_loc: thay.append("Mã **rời** danh sách đạt lọc chất lượng: " + ", ".join(sorted(cu_loc - moi_loc)))
    cham_moi = {x["ma"] for x in sl.get("bctc_cham", [])} - set(cu.get("bctc_cham", []))
    if cham_moi: thay.append("Mã **mới chậm công bố BCTC**: " + ", ".join(sorted(cham_moi)))
    moi_bc = {x["ma"] for x in sl.get("bctc_moi_7_ngay", [])} - set(cu.get("bctc_moi", []))
    if moi_bc: thay.append("BCTC **mới công bố**: " + ", ".join(sorted(moi_bc)))
    return thay, False


def luu_trang_thai(sl):
    with open(FILE_TRANG_THAI, "w") as f:
        json.dump({"ngay": sl["ngay_du_lieu"], "tren_ma200": sl["tang3"]["tren_ma200"], "tat_ca_dat_loc": sl["tat_ca_dat_loc"],
                   "bctc_cham": [x["ma"] for x in sl.get("bctc_cham", [])], "bctc_moi": [x["ma"] for x in sl.get("bctc_moi_7_ngay", [])]}, f, ensure_ascii=False)


# ---------------------------------------------------------------- dựng báo cáo
def huong_dan_ngan(t3):
    return "giải ngân lõi như bình thường" if t3["tren_ma200"] else "tạm dừng mua thêm lõi"


def huong_dan(t3):
    if t3["tren_ma200"]:
        return "Giải ngân lõi như bình thường: mua đều E1VFVN30 vào phiên đầu tháng."
    return "VN-Index dưới MA200: tạm dừng mua thêm lõi (giữ tiền mặt), không bán. Mua lại khi VN-Index vượt MA200."


def dung_markdown(sl, loi_binh, thay_doi, lan_dau, link=None):
    t3 = sl["tang3"]
    d = [f"# Báo cáo Quant V34 – dữ liệu phiên {sl['ngay_du_lieu']}", ""]
    if link: d += [f"Xem trực tuyến: {link}", ""]
    d += ["## 0. Thay đổi so với báo cáo trước", ""]
    if lan_dau: d.append("Đây là báo cáo đầu tiên có theo dõi thay đổi; từ lần sau sẽ so sánh với báo cáo này.")
    elif thay_doi: d += [f"- {x}" for x in thay_doi]
    else: d.append("Không có thay đổi: tín hiệu MA200, danh sách đạt lọc và tình trạng BCTC giữ nguyên.")
    d += ["", "## 1. Tầng 3: luật thị trường", "",
          f"- VN-Index **{t3['vnindex']}**, MA200 **{t3['ma200']}** ({t3['cach_ma200_pct']:+.2f}%), đã {'trên' if t3['tren_ma200'] else 'dưới'} MA200 {t3['so_phien_cung_phia']} phiên liên tiếp.",
          f"- **Hướng dẫn: {huong_dan(t3)}**", "",
          "Chỉ báo tham khảo (backtest cho thấy không cải thiện lợi suất so với luật MA200, không dùng để ra quyết định):", "",
          "| Chỉ báo | Giá trị |", "| --- | ---: |",
          f"| Độ rộng: % mã trên MA200 ({t3['do_rong_so_ma']} mã thanh khoản) | {t3['do_rong_ma200_pct']}% |",
          f"| Độ rộng: % mã trên MA50 | {t3['do_rong_ma50_pct']}% |",
          f"| Biến động 20 phiên (năm hóa) | {t3['bien_dong_20p_pct']}% (gấp {t3['bien_dong_ty_le']} lần trung vị 1 năm) |",
          f"| Cách đỉnh 52 tuần | {t3['cach_dinh_52t_pct']:+.1f}% |", ""]
    d += ["## 2. Tầng 1: lõi và phân bổ", "",
          "- Lõi **100% E1VFVN30** (mua đều hằng tháng). Vệ tinh đã bỏ vì backtest không cải thiện (xem mục 6).", f"- {huong_dan(t3)}"]
    if sl.get("vi_the"):
        d += ["", "| Mã | Số lượng | Giá (nghìn đồng) | Giá trị (đồng) |", "| --- | ---: | ---: | ---: |"]
        d += [f"| {r['ma']} | {r['so_luong']:,} | {r['gia']} | {r['gia_tri']:,.0f} |" for r in sl["vi_the"]]
        d += ["", f"- Tiền mặt: {sl['tien_mat']:,.0f} đồng; tỷ lệ tiền mặt: **{sl['ty_le_tien_mat_pct']}%**."]
    else:
        d.append("- Chưa có `data/vi_the.json` nên không có bảng vị thế và tỷ lệ tiền mặt (không có dữ liệu).")
    d += ["", "## 3. Tầng 2: danh sách chất lượng (chỉ theo dõi)", "",
          f"Có **{sl['so_ma_dat_loc']}/{sl['so_ma_thanh_khoan']}** mã thanh khoản qua các phép thử tự động (dòng tiền kinh doanh, phải thu và tồn kho, lãi bất thường, nợ vay, bán ròng nội bộ, cổ tức tiền thật, BCTC không quá cũ; ngân hàng có bộ riêng). "
          "Backtest dài hạn (2010–2026, 866 mã gồm cả mã đã hủy niêm yết) cho thấy lõi chọn mã **ngang** chuẩn mua đều có cổ tức, chưa có ý nghĩa thống kê: đây là danh sách theo dõi, không phải khuyến nghị mua. Chưa đánh giá: ý kiến kiểm toán thật, cầm cố/ký quỹ (không có nguồn dữ liệu).", ""]
    if sl["danh_sach_chat_luong"]:
        d += ["| Mã | Ngành | Điểm | ROE TB (%) | Cổ tức tiền (năm/5) | Phép thử đạt/đánh giá được |", "| --- | --- | ---: | ---: | ---: | ---: |"]
        d += [f"| {r['ma']} | {r['nganh']} | {r['diem']} | {r['roe_tb']} | {r['co_tuc_tien_5nam'] if r['co_tuc_tien_5nam'] is not None else '–'} | {r['dat']}/{r['danh_gia']} |" for r in sl["danh_sach_chat_luong"]]
    d += ["", "## 4. Dữ liệu: BCTC mới và mã chậm công bố", ""]
    if "bctc_moi_7_ngay" in sl:
        moi = sl["bctc_moi_7_ngay"]
        d.append("- BCTC mới công bố trong 7 ngày: " + (", ".join(f"{x['ma']} ({x['ky']}, công bố {x['cong_bo']})" for x in moi) if moi else "không có") + ".")
        cham = sl.get("bctc_cham", [])
        d.append("- Mã chậm công bố (quá hạn quý +45 ngày hoặc năm +90 ngày, đang niêm yết): " + (", ".join(f"{x['ma']} (kỳ cuối {x['ky_cuoi']}, cần {x['ky_ky_vong']})" for x in cham[:25]) + ("…" if len(cham) > 25 else "") if cham else "không có") + ". Chậm nộp BCTC là một dấu hiệu cảnh báo.")
        d.append(f"- Dữ liệu BCTC cập nhật lần cuối: {sl.get('bctc_cap_nhat')}.")
    else:
        d.append("- Chưa có dữ liệu cập nhật BCTC (không có dữ liệu).")
    d.append(f"- Giá: {sl['gia_moi']} mã tải mới từ Entrade, {sl['gia_cu']} mã dùng dữ liệu đã lưu; theo dõi {sl['so_ma_theo_doi']} mã đang niêm yết.")
    d += ["", "## 5. Lời bình", "", loi_binh or "Không có lời bình (không có khóa Gemini hoặc lỗi gọi mô hình).", "",
          "## 6. Tình trạng các tầng", "",
          "| Tầng | Trạng thái | Kết quả backtest |", "| --- | --- | --- |",
          "| 1. Lõi | Dùng: E1VFVN30 mua đều hằng tháng | Chuẩn so sánh |",
          "| 2. Chọn mã | Chỉ theo dõi | Ngang chuẩn có cổ tức (2010→nay: +0,52 điểm %/năm, khoảng tin cậy [−3,4; +4,7]) |",
          "| 3. Luật thị trường | Dùng: tạm dừng mua khi dưới MA200 | CAGR ngang chuẩn, giảm MDD ở đợt giảm lớn |",
          "| 4. Vệ tinh Wyckoff | Đã bỏ | Không cải thiện, chi phí cao hơn |", "",
          "_Công cụ nghiên cứu cá nhân, không phải tư vấn đầu tư._"]
    return "\n".join(d)


def viet_loi_binh(sl, thay_doi):
    key = os.environ.get("GEMINI_API_KEY")
    if not key: return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
    except Exception:
        return None
    t3 = sl["tang3"]
    tom_tat = {"ngay_du_lieu": sl["ngay_du_lieu"], "vnindex": t3["vnindex"], "ma200": t3["ma200"], "tren_ma200": t3["tren_ma200"], "cach_ma200_pct": t3["cach_ma200_pct"],
               "so_phien_cung_phia_ma200": t3["so_phien_cung_phia"], "do_rong_ma200_pct": t3["do_rong_ma200_pct"], "bien_dong_ty_le": t3["bien_dong_ty_le"], "cach_dinh_52t_pct": t3["cach_dinh_52t_pct"],
               "so_ma_dat_loc": sl["so_ma_dat_loc"], "so_ma_thanh_khoan": sl["so_ma_thanh_khoan"], "so_thay_doi_so_voi_lan_truoc": len(thay_doi), "ty_le_tien_mat_pct": sl.get("ty_le_tien_mat_pct")}
    prompt = ("Viết lời bình ngắn (tối đa 130 từ, tiếng Việt có dấu) cho báo cáo đầu tư dài hạn. CHỈ dùng các số liệu trong JSON sau; "
              "không tìm kiếm, không thêm số liệu hay tin tức nào khác; trường nào là null thì ghi 'không có dữ liệu'. Không khuyến nghị mua bán cụ thể.\n" + json.dumps(tom_tat, ensure_ascii=False))
    for m in MODELS:
        try: return genai.GenerativeModel(m).generate_content(prompt).text
        except Exception as e: print(f"⚠️ Gemini {m}: {type(e).__name__}")
    return None


def link_trang():
    repo, nhanh = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_REF_NAME")
    return f"https://github.com/{repo}/blob/{nhanh}/docs/BAO_CAO_MOI_NHAT.md" if repo and nhanh else None


def gui_mail(tieu_de, noi_dung):
    user, pw = os.environ.get("EMAIL_USER", ""), os.environ.get("EMAIL_PASS", "")
    nhan = [x.strip() for x in (os.environ.get("EMAIL_NHAN") or user).split(",") if x.strip()]
    if not user or not pw or not nhan:
        print("⚠️ Bỏ qua gửi Email vì chưa cấu hình tài khoản."); return
    import markdown
    html = markdown.markdown(noi_dung, extensions=["tables"])
    css = "table{border-collapse:collapse}th,td{border:1px solid #ccc;padding:4px 8px}th{background:#f0f0f0}"
    msg = MIMEMultipart("alternative"); msg["From"], msg["To"], msg["Subject"] = user, ", ".join(nhan), tieu_de
    msg.attach(MIMEText(noi_dung, "plain")); msg.attach(MIMEText(f"<html><head><style>{css}</style></head><body style='font-family:Segoe UI,Arial,sans-serif'>{html}</body></html>", "html"))
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
    thay, lan_dau = so_sanh_trang_thai(doc_trang_thai(), sl)
    bc = dung_markdown(sl, viet_loi_binh(sl, thay), thay, lan_dau, link_trang())
    print(bc)
    if "--xuat-trang" in sys.argv:
        os.makedirs(os.path.dirname(FILE_TRANG), exist_ok=True); open(FILE_TRANG, "w").write(bc + "\n")
    if "--luu-trang-thai" in sys.argv: luu_trang_thai(sl)
    if not khong_gui: gui_mail(os.environ.get("TIEN_TO_TIEU_DE", "") + f"Quant V34 – {sl['ngay_du_lieu']}", bc)
