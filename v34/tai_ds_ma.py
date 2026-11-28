"""Làm mới danh sách mã niêm yết đầy đủ từ Vietcap (yêu cầu thường), lưu bản gọn data/ds_ma.json."""
import json, os, requests
from collections import Counter
H = {"User-Agent": "quant-agent-research/1.0", "Accept": "application/json"}
def main():
    r = requests.get("https://trading.vietcap.com.vn/api/price/symbols/getAll", headers=H, timeout=60)
    print("HTTP", r.status_code, len(r.text), flush=True)
    j = r.json()
    gon = [{"ma": x.get("symbol"), "loai": x.get("type"), "san": x.get("board"), "ten": x.get("organShortName"), "icb2": x.get("icbCode2")} for x in j if x.get("symbol")]
    print("tổng:", len(gon), "| theo (loại, sàn):", Counter((x["loai"], x["san"]) for x in gon).most_common(15), flush=True)
    print("khóa gốc:", sorted(j[0].keys()), flush=True)
    json.dump(gon, open("data/ds_ma.json", "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
