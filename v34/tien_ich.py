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
