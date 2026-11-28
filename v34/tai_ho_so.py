"""Tải hồ sơ công ty (ngành, nhóm sàn, số cổ phiếu) từ Vietcap IQ cho mọi mã có BCTC (yêu cầu thường, nghỉ giữa các lệnh)."""
import glob, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tai_du_lieu as td
os.makedirs(f"{td.DATA}/ho_so", exist_ok=True)
def _chay():
    loi = []
    for f in sorted(glob.glob(f"{td.DATA}/bctc/[A-Z]*.json")):
        ma = os.path.basename(f)[:-5]
        d = td.tai_iq(f"{td.IQ}/company/{ma}"); time.sleep(0.3)
        if not d: loi.append(ma); print("thiếu", ma, flush=True); continue
        khoa = ["organCode", "ticker", "sector", "sectorVn", "comGroupCode", "comTypeCode", "icbCodeLv1", "icbCodeLv2", "icbCodeLv3", "icbCodeLv4", "issueShare", "numberOfSharesMktCap", "viOrganShortName"]
        json.dump({k: d.get(k) for k in khoa}, open(f"{td.DATA}/ho_so/{ma}.json", "w"), ensure_ascii=False); print("ho_so", ma, d.get("sector"), flush=True)
    json.dump({"loi": loi}, open(f"{td.DATA}/_trang_thai_ho_so.json", "w"))


if __name__ == "__main__":
    _chay()
