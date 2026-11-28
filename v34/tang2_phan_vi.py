"""Bộ lọc theo phân vị (đặt trước): thay ngưỡng tuyệt đối của phép thử 1 và 2 bằng thứ hạng trong nhóm phi ngân hàng tại cùng thời điểm.
OCF/LNST phải >= phân vị 40; mức tăng phải thu và tồn kho vượt tăng doanh thu phải <= phân vị 60. Các phép thử khác như bộ lọc TTM."""
import numpy as np
from tang2_ttm import *


def tao_loc_phan_vi(dl, p_ocf=40, p_pt=60):
    cache = {}
    def cat(ngay):
        if ngay in cache: return cache[ngay]
        oc, pt = [], []
        for m in dl.nam:
            if m in NGAN_HANG: continue
            kq, nt = phep_thu_ttm(dl, m, ngay)
            if nt is None: continue
            if np.isfinite(nt["ty_ocf"]): oc.append(nt["ty_ocf"])
            if np.isfinite(nt["ty_pt"]): pt.append(nt["ty_pt"])
        cache[ngay] = (np.percentile(oc, p_ocf) if oc else -np.inf, np.percentile(pt, p_pt) if pt else np.inf)
        return cache[ngay]
    def loc_pv(dl_, ma, ngay):
        if ma in NGAN_HANG: return loc_ttm(dl_, ma, ngay)
        kq, nt = phep_thu_ttm(dl_, ma, ngay)
        if kq is None: return False, {"du_lieu": "thiếu lịch sử"}, None
        t_oc, t_pt = cat(ngay)
        kq["1_ocf_lnst"] = bool(nt["ty_ocf"] >= t_oc and nt["lnst"] > 0) if np.isfinite(nt["ty_ocf"]) else False
        kq["2_phai_thu_ton_kho"] = bool(nt["ty_pt"] <= t_pt) if np.isfinite(nt["ty_pt"]) else CHUA_DANH_GIA
        return all(v is True for v in kq.values() if v != CHUA_DANH_GIA), kq, nt
    return loc_pv
