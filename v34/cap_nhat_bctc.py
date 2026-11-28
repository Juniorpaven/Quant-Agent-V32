"""Cập nhật gia tăng BCTC (Vietcap IQ, yêu cầu thường): mỗi mã hỏi 1 lệnh kết quả kinh doanh; chỉ tải lại đầy đủ khi có kỳ mới hoặc ngày công bố đổi.
Phát hiện mã chậm công bố (quý quá hạn 45 ngày, năm quá hạn 90 ngày). Giao dịch nội bộ làm mới mỗi thứ Hai và khi có BCTC mới.
Ghi data/_bctc_moi.json cho báo cáo hằng ngày. Gặp 403/429 thì dừng."""
import glob, json, os, sys, time
from datetime import datetime, timedelta, timezone
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_du_lieu as td
from tien_ich import ghi_bctc_manh, ghi_noibo
import tai_mo_rong as mr

DATA = td.DATA


def ky_moi_nhat(kqkd):
    q = [r for r in ((kqkd or {}).get("quarters") or []) if r.get("lengthReport") in (1, 2, 3, 4)]
    if not q: return None
    r = max(q, key=lambda r: (r["yearReport"], r["lengthReport"]))
    return (int(r["yearReport"]), int(r["lengthReport"]), (r.get("publicDate") or "")[:10])


def ky_ky_vong(hom_nay):
    """Quý gần nhất đã quá hạn công bố (quý +45 ngày; quý 4 +90 ngày do báo cáo năm kiểm toán)."""
    for y in (hom_nay.year, hom_nay.year - 1):
        for q in (4, 3, 2, 1):
            cuoi = pd.Timestamp(y, q * 3, 1) + pd.offsets.MonthEnd(0)
            han = cuoi + pd.Timedelta(days=90 if q == 4 else 45)
            if han < hom_nay: return (y, q)
    return None


def main():
    hom_nay = pd.Timestamp(datetime.now(timezone.utc).date())
    thu_hai = hom_nay.weekday() == 0
    moi, loi, cham = [], [], []
    san = {x["ma"]: x["san"] for x in json.load(open(f"{DATA}/ds_ma.json"))} if os.path.exists(f"{DATA}/ds_ma.json") else {}
    ky_kv = ky_ky_vong(hom_nay)
    for f in sorted(glob.glob(f"{DATA}/bctc/[A-Z]*.json")):
        ma = os.path.basename(f)[:-5]
        cu = json.load(open(f)); ky_cu = ky_moi_nhat(cu.get("kqkd"))
        niem_yet = san.get(ma) in ("HSX", "HNX")      # đang niêm yết theo danh sách mã (làm mới hằng tháng)
        kq = td.tai_iq(f"{td.IQ}/company/{ma}/financial-statement?section=INCOME_STATEMENT"); time.sleep(0.15)
        if kq is None: loi.append(ma); continue
        ky_m = ky_moi_nhat(kq)
        if ky_m and (not ky_cu or ky_m[:2] > ky_cu[:2] or ky_m[2] != ky_cu[2]):
            out = {"kqkd": kq}
            for khoa, sec in (("cdkt", "BALANCE_SHEET"), ("lctt", "CASH_FLOW")): out[khoa] = td.tai_iq(f"{td.IQ}/company/{ma}/financial-statement?section={sec}"); time.sleep(0.3)
            out["chi_so"] = td.tai_iq(f"{td.IQ}/company/{ma}/statistics-financial"); time.sleep(0.3)
            if out["cdkt"] and out["lctt"]:
                ghi_bctc_manh(f, out)
                moi.append({"ma": ma, "ky": f"Q{ky_m[1]}/{ky_m[0]}", "cong_bo": ky_m[2], "truoc": f"Q{ky_cu[1]}/{ky_cu[0]}" if ky_cu else None})
                ky_cu = ky_m
        if niem_yet and ky_kv and ky_cu and ky_cu[:2] < ky_kv: cham.append({"ma": ma, "ky_cuoi": f"Q{ky_cu[1]}/{ky_cu[0]}" if ky_cu else None, "ky_ky_vong": f"Q{ky_kv[1]}/{ky_kv[0]}"})
        if thu_hai or any(m["ma"] == ma for m in moi):
            ev = mr.tai_noi_bo(ma)
            if ev: ghi_noibo(f"{DATA}/noibo/{ma}.json", ev)
            time.sleep(0.3)
    f_ls = f"{DATA}/_bctc_moi.json"
    ls = json.load(open(f_ls)).get("lich_su", []) if os.path.exists(f_ls) else []
    ls = [x for x in ls if pd.Timestamp(x["ngay"]) >= hom_nay - pd.Timedelta(days=60)] + [dict(ngay=str(hom_nay.date()), ma=m["ma"], ky=m["ky"], cong_bo=m["cong_bo"]) for m in moi]
    json.dump({"cap_nhat": datetime.now(timezone.utc).isoformat(), "moi_hom_nay": moi, "cham_cong_bo": cham, "loi": loi, "lich_su": ls}, open(f_ls, "w"), ensure_ascii=False, indent=1)
    print(f"Mới: {len(moi)} | chậm công bố: {len(cham)} | lỗi: {len(loi)}")
    for m in moi: print("  mới", m)
    for c in cham[:30]: print("  chậm", c)


if __name__ == "__main__":
    main()
