"""Tiện ích ghi dữ liệu gọn: bỏ các trường BCTC toàn 0/trống trừ các trường mà bộ lọc dùng, ghi JSON không khoảng trắng."""
import json
DUNG = {"isa3", "isa8", "isa14", "isa16", "isa20", "isa22", "bsa8", "bsa11", "bsa13", "bsa15", "bsa26", "bsa53", "bsa56", "bsa71", "bsa78", "bsa159", "bsa162", "cfa18", "cfa32"}
META = {"organCode", "ticker", "yearReport", "lengthReport", "publicDate"}


def gon(o):
    if isinstance(o, dict):
        r = {}
        for k, v in o.items():
            if isinstance(v, (dict, list)): r[k] = gon(v)
            elif k in DUNG or k in META or v not in (None, 0, 0.0, ""): r[k] = v
        return r
    if isinstance(o, list): return [gon(x) for x in o]
    return o


def ghi_bctc(duong_dan, out):
    """out: dict gồm kqkd, cdkt, lctt (được gọn) và chi_so (giữ nguyên)."""
    g = {k: (gon(v) if k in ("kqkd", "cdkt", "lctt") else v) for k, v in out.items()}
    with open(duong_dan, "w") as f: json.dump(g, f, ensure_ascii=False, separators=(",", ":"))


# ---------- nén cho tập mã lớn ----------
KQKD_MA = {"10", "24", "40", "50", "60", "61", "70"}
CDKT_MA = {"130", "140", "270", "300", "320", "338", "400", "440"}
LCTT_MA = {"HDKD_20", "HDTC_36"}
CHI_SO_KHOA = {"year", "quarter", "yearReport", "roe", "npl", "loansLossReservesToNPLs", "loansGrowth", "pe", "pb", "numberOfSharesMktCap", "marketCap"}


def _ky(p, giu):
    return {"year": p.get("year"), "content": p.get("content") or "", "data": [{"code": c["code"], "value": c["value"]} for c in (p.get("data") or []) if c.get("code") in giu and c.get("value") is not None]}


def gon_cafef_bc(v, giu, theo_phan_doan):
    """Giữ cấu trúc của CafeF nhưng chỉ các mã dòng cần dùng."""
    if not v or not v.get("data"): return {"data": []}
    if theo_phan_doan: return {"data": [{"code": x.get("code"), "data": [_ky(p, giu) for p in (x.get("data") or [])]} for x in v["data"]]}
    return {"data": [_ky(x, giu) for x in v["data"]]}


def ghi_cafef(duong_dan, out):
    g = {"kqkd": gon_cafef_bc(out.get("kqkd"), KQKD_MA, False), "cdkt": gon_cafef_bc(out.get("cdkt"), CDKT_MA, True), "lctt": gon_cafef_bc(out.get("lctt"), LCTT_MA, True),
         "co_tuc": [e for e in (out.get("co_tuc") or []) if e.get("type") == 1]}
    with open(duong_dan, "w") as f: json.dump(g, f, ensure_ascii=False, separators=(",", ":"))


def gon_noibo(events):
    """Chỉ giữ (ngày công bố, số cổ phiếu bán ròng) của giao dịch đã thực hiện; mua mang dấu âm."""
    ev = []
    for x in events or []:
        if x.get("tradeStatusEn") != "Done" or x.get("actionTypeEn") not in ("Buy", "Sell") or not x.get("publicDate"): continue
        acq = x.get("shareAcquire") or 0.0
        if x["actionTypeEn"] == "Sell": sl = -acq if acq < 0 else max((x.get("shareBeforeTrade") or 0) - (x.get("shareAfterTrade") or 0), 0)
        else: sl = -(acq if acq > 0 else max((x.get("shareAfterTrade") or 0) - (x.get("shareBeforeTrade") or 0), 0))
        ev.append([x["publicDate"][:10], float(sl)])
    return {"v": 2, "ev": ev}


def ghi_noibo(duong_dan, events):
    with open(duong_dan, "w") as f: json.dump(gon_noibo(events), f, separators=(",", ":"))


def ghi_chi_so_gon(out):
    out = dict(out); out["chi_so"] = [{k: v for k, v in r.items() if k in CHI_SO_KHOA} for r in (out.get("chi_so") or [])]
    return out


def ghi_gia_gz(duong_dan, df):
    df = df.copy(); df["Volume"] = df["Volume"].round(0).astype("int64")
    df.to_csv(duong_dan, index=False, float_format="%.3f", compression="gzip")


def gon_manh(o):
    """Chỉ giữ các trường BCTC mà bộ lọc dùng (và trường meta)."""
    if isinstance(o, dict):
        return {k: (gon_manh(v) if isinstance(v, (dict, list)) else v) for k, v in o.items() if isinstance(v, (dict, list)) or k in DUNG or k in META}
    if isinstance(o, list): return [gon_manh(x) for x in o]
    return o


def ghi_bctc_manh(duong_dan, out):
    g = {k: (gon_manh(v) if k in ("kqkd", "cdkt", "lctt") else v) for k, v in ghi_chi_so_gon(out).items()}
    with open(duong_dan, "w") as f: json.dump(g, f, ensure_ascii=False, separators=(",", ":"))
