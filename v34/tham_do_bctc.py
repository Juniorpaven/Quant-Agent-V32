"""Thăm dò nguồn BCTC công khai (VNDirect finfo, SSI) bằng yêu cầu bình thường, không giả header trình duyệt."""
import os, requests
os.makedirs("data/tham_do", exist_ok=True)
H = {"User-Agent": "quant-agent-v34-research/1.0"}
UNG_VIEN = {
 "vnd_ratios_latest": "https://finfo-api.vndirect.com.vn/v4/ratios/latest?filter=code:FPT",
 "vnd_fs_quy": "https://finfo-api.vndirect.com.vn/v4/financial_statements?q=code:FPT~reportType:QUARTER&sort=fiscalDate&size=30",
 "vnd_fs_nam": "https://finfo-api.vndirect.com.vn/v4/financial_statements?q=code:FPT~reportType:ANNUAL&sort=fiscalDate&size=30",
 "vnd_co_tuc": "https://finfo-api.vndirect.com.vn/v4/events?q=code:FPT~type:DIVIDEND&size=30",
 "ssi_bang_can_doi": "https://fiin-fundamental.ssi.com.vn/FinancialStatement/GetBalanceSheet?language=vi&OrganCode=FPT&Skip=0&Frequency=Yearly&Top=10",
 "ssi_kqkd": "https://fiin-fundamental.ssi.com.vn/FinancialStatement/GetIncomeStatement?language=vi&OrganCode=FPT&Skip=0&Frequency=Yearly&Top=10",
}
for ten, url in UNG_VIEN.items():
    try:
        r = requests.get(url, headers=H, timeout=15)
        mo_ta = f"{r.status_code} {r.headers.get('content-type','')} len={len(r.text)}"
        open(f"data/tham_do/{ten}.txt", "w").write(mo_ta + "\n" + r.text[:4000])
    except Exception as e:
        mo_ta = f"LỖI {type(e).__name__} {e}"
    print(ten, mo_ta, flush=True)
