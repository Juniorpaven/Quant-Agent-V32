"""Tầng 2 phiên bản TTM: bộ lọc dùng dữ liệu bốn quý gần nhất (cập nhật đến quý mới nhất đã công bố) thay vì báo cáo năm,
cộng hai phép thử thay thế: (4) tỷ lệ phải thu nội bộ và cho vay trên tổng tài sản; (5) chênh lệch tổng 4 quý và số năm đã kiểm toán."""
import glob, json, os
import numpy as np, pandas as pd
from tang2_chon_ma import DuLieuCoBan, NGAN_HANG, CHUA_DANH_GIA, _g, _phep_thu_noi_bo, phep_thu_ngan_hang
from du_lieu_dai import doc_co_tuc


def _qkey(r): return (int(r["yearReport"]), int(r["lengthReport"]))


class DuLieuTTM(DuLieuCoBan):
    def __init__(self, thu_muc="data/bctc"):
        super().__init__(thu_muc)
        self.ttm, self.lech_kt, self.co_tuc = {}, {}, {}
        for f in glob.glob(os.path.join(os.path.dirname(thu_muc), "cafef", "[A-Z]*.json")):
            try: self.co_tuc[os.path.basename(f)[:-5]] = doc_co_tuc(json.load(open(f)).get("co_tuc"))
            except Exception: pass
        for ma in self.nam:
            d = json.load(open(os.path.join(thu_muc, f"{ma}.json")))
            qi = {_qkey(r): r for r in (d["kqkd"].get("quarters") or []) if r["lengthReport"] in (1, 2, 3, 4)}
            qb = {_qkey(r): r for r in (d["cdkt"].get("quarters") or []) if r["lengthReport"] in (1, 2, 3, 4)}
            qc = {_qkey(r): r for r in (d["lctt"].get("quarters") or []) if r["lengthReport"] in (1, 2, 3, 4)}
            nc = {int(r["yearReport"]): r for r in (d["lctt"].get("years") or [])}
            snap = {}
            for (y, q), r in qi.items():
                if (y, q) not in qb or (y, q) not in qc: continue
                ky = [((y - 1, q + 4 - k) if q - k <= 0 else (y, q - k)) for k in range(4)]
                if any(k not in qi for k in ky): continue
                if (y - 1) not in nc or (y - 1, q) not in qc: continue
                tt = lambda f: sum(_g(qi[k], f) for k in ky)
                ytd = lambda f: _g(qc[(y, q)], f) + _g(nc[y - 1], f) - _g(qc[(y - 1, q)], f)
                b = qb[(y, q)]
                cuoi_q = pd.Timestamp(y, q * 3, 1) + pd.offsets.MonthEnd(0)
                pub = pd.Timestamp(r["publicDate"]) if r.get("publicDate") else None
                # ngày công bố sau cuối quý hơn 120 ngày là công bố lại/điều chỉnh: dùng ngày theo quy tắc (quý +45 ngày), không dùng ngày điều chỉnh
                hl = cuoi_q + pd.Timedelta(days=45) if (pub is None or pub > cuoi_q + pd.Timedelta(days=120)) else max(pub, cuoi_q + pd.Timedelta(days=30))
                snap[(y, q)] = {"hl": hl, "isa3": tt("isa3"), "lnst": tt("isa22"), "pbt": tt("isa16"), "lai": tt("isa8"), "tn_khac": tt("isa14"),
                                "ocf": ytd("cfa18"), "pt": _g(b, "bsa8"), "tk": _g(b, "bsa15"), "vcsh": _g(b, "bsa78"),
                                "vay": np.nansum([_g(b, "bsa56"), _g(b, "bsa71")]), "tong_ts": _g(b, "bsa53"),
                                "lien_quan": np.nansum([_g(b, "bsa11"), _g(b, "bsa26"), _g(b, "bsa159"), _g(b, "bsa162")])}
            self.ttm[ma] = snap
            # chênh lệch tổng 4 quý so với số năm đã kiểm toán
            self.lech_kt[ma] = {}
            for y, rn in {r["yearReport"]: r for r in d["kqkd"]["years"]}.items():
                if all((y, k) in qi for k in (1, 2, 3, 4)) and rn.get("isa22") is not None:
                    tq = sum(_g(qi[(y, k)], "isa22") for k in (1, 2, 3, 4))
                    dt = max(abs(_g(rn, "isa22")), 0.02 * abs(_g(rn, "isa3")))
                    self.lech_kt[ma][y] = (abs(tq - _g(rn, "isa22")) / dt if dt > 0 else np.nan, self.nam[ma][y]["hieu_luc"])

    def snapshots(self, ma, ngay, n=4):
        s = self.ttm.get(ma, {}); ds = sorted(k for k, v in s.items() if v["hl"] <= ngay)
        if not ds: return None
        y, q = ds[-1]
        ks = [(y - i, q) for i in range(n)]
        return [s[k] for k in reversed(ks) if k in s and s[k]["hl"] <= ngay]


def phep_thu_ttm(dl, ma, ngay, moi=True):
    sn = dl.snapshots(ma, ngay, 4)
    if not sn or len(sn) < 3: return None, None
    cur, base = sn[-1], sn[0]
    kq = {}
    df = pd.DataFrame(sn)
    ln = df.lnst.sum()
    kq["1_ocf_lnst"] = bool(ln > 0 and df.ocf.sum() / ln >= 0.8 and (df.ocf < 0).sum() <= 1)
    ts0, ts1 = base["pt"] + base["tk"], cur["pt"] + cur["tk"]
    kq["2_phai_thu_ton_kho"] = bool(ts1 / ts0 - 1 <= (cur["isa3"] / base["isa3"] - 1) + 0.15) if base["isa3"] > 0 and ts0 > 0 else CHUA_DANH_GIA
    ty = (df.tn_khac / df.pbt).replace([np.inf, -np.inf], np.nan)
    kq["3_bat_thuong"] = bool(ty.mean() < 0.15) if ty.notna().sum() >= 2 else CHUA_DANH_GIA
    # 4: tỷ lệ phải thu nội bộ và cho vay / tổng tài sản
    r_now = cur["lien_quan"] / cur["tong_ts"] if cur["tong_ts"] > 0 else np.nan
    r_old = base["lien_quan"] / base["tong_ts"] if base["tong_ts"] > 0 else np.nan
    kq["4_ben_lien_quan_thay_the"] = bool(not (r_now > 0.10 and r_now - r_old > 0.03)) if np.isfinite(r_now) and np.isfinite(r_old) else CHUA_DANH_GIA
    # 5: chênh lệch tổng 4 quý và số năm kiểm toán, hai năm gần nhất đã công bố
    lk = {y: v for y, v in dl.lech_kt.get(ma, {}).items() if v[1] <= ngay and np.isfinite(v[0])}
    gan = [lk[y][0] for y in sorted(lk)[-2:]]
    kq["5_kiem_toan_thay_the"] = bool(max(gan) <= 0.10) if gan else CHUA_DANH_GIA
    lai = abs(cur["lai"]) if np.isfinite(cur["lai"]) else 0.0
    cover = (cur["pbt"] + lai) / lai if lai > 0 else np.inf
    kq["6_no_vay"] = bool(cover >= 3 and (cur["vay"] / cur["vcsh"] if cur["vcsh"] > 0 else np.inf) <= 1.5)
    kq["7_noi_bo"] = _phep_thu_noi_bo(dl, ma, ngay)
    nam = dl.cac_nam(ma, ngay, 5)
    ct = dl.co_tuc.get(ma)
    if ct is not None and len(ct) and ngay >= pd.Timestamp(2018, 1, 1):   # cổ tức tiền thật theo ngày không hưởng quyền (CafeF)
        d5 = ct[(ct.loai == "tien") & (ct.ngay <= ngay) & (ct.ngay > ngay - pd.Timedelta(days=365 * 5))]; so_nam = int(d5.ngay.dt.year.nunique())
    else:
        so_nam = int(sum(1 for y, v in nam if _g(v["lctt"], "cfa32") < 0)) if nam else 0   # thay thế khi chưa có dữ liệu cổ tức
    kq["8_co_tuc_tien_mat"] = bool(so_nam >= 4)
    kq["0_bctc_moi"] = bool(cur["hl"] >= ngay - pd.Timedelta(days=200))
    roe = (df.lnst / df.vcsh).mean()
    return kq, {"roe": roe, "ocf_ln": df.ocf.sum() / ln if ln > 0 else np.nan, "lnst": cur["lnst"], "so_nam_cotuc": so_nam, "ty_ocf": df.ocf.sum() / ln if ln > 0 else np.nan, "ty_pt": (ts1 / ts0 - 1) - (cur["isa3"] / base["isa3"] - 1) if base["isa3"] > 0 and ts0 > 0 else np.nan}


# Kiểm chứng 2010–2026 (docs/ket_qua_chi_bao_nong_noi_bo_20261128.txt) không thấy giá trị của phép thử nội bộ: chỉ hiển thị cảnh báo, không loại mã.
NOI_BO_CHI_CANH_BAO = True


def loc_ttm(dl, ma, ngay):
    if ma in NGAN_HANG:
        kq, nt = phep_thu_ngan_hang(dl, ma, ngay)
    else:
        kq, nt = phep_thu_ttm(dl, ma, ngay)
    if kq is None: return False, {"du_lieu": "thiếu lịch sử"}, None
    return all(v is True for k, v in kq.items() if v != CHUA_DANH_GIA and not (NOI_BO_CHI_CANH_BAO and k == "7_noi_bo")), kq, nt
