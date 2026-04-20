import requests
import time
import pandas as pd
import yfinance as yf

def check_cash_flow_tcbs(ticker):
    """
    Tầng 1: Soi BCTC bằng API Server AWS nội bộ của TCBS (Siêu ổn định).
    Quét dữ liệu Lưu chuyển tiền tệ (Cash Flow) theo Quý.
    """
    url = f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ticker}/cashflow?yearly=0&isAll=false"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if res.status_code != 200: 
            return fallback_cash_flow_yfinance(ticker) # Chuyển súng nếu TCBS bảo trì
            
        data = res.json()
        if not data: return "⚠️ Không có BCTC Quý gần nhất."
        
        # Lấy quý gần nhất
        latest_quarter = data[0]
        op_cashflow = latest_quarter.get('fromSale', 0) # Dòng tiền từ hoạt động kinh doanh
        
        if op_cashflow < 0:
            return f"❌ CẢNH BÁO ĐỎ: Dòng tiền Kinh doanh đang ÂM ({op_cashflow} tỷ). Công ty đang bị 'chảy máu' tiền mặt."
        else:
            return "✅ Dòng tiền Kinh doanh DƯƠNG. Mạch máu tài chính khỏe mạnh."
            
    except Exception as e:
        return fallback_cash_flow_yfinance(ticker)

def fallback_cash_flow_yfinance(ticker):
    """Kế hoạch B: Nếu API TCBS lỗi, dùng YFinance để vét đáy"""
    try:
        stock = yf.Ticker(f"{ticker}.VN")
        cf = stock.cash_flow
        if cf.empty: return "⚠️ Không cào được dữ liệu BCTC."
        
        op_cashflow = cf.loc['Operating Cash Flow'].iloc[0]
        if op_cashflow < 0:
            return "❌ CẢNH BÁO ĐỎ: Dòng tiền Kinh doanh ÂM (Theo dữ liệu YFinance)."
        return "✅ Dòng tiền Kinh doanh DƯƠNG."
    except:
        return "⚠️ Lỗi trích xuất BCTC từ mọi nguồn."

def check_intraday_distribution(ticker):
    """
    Tầng 2: Soi Phân phối ngầm Intraday (Dùng Entrade có rào chắn thép)
    """
    end_time = int(time.time())
    start_time = end_time - (3 * 24 * 60 * 60) # Cắt lớp 3 ngày gần nhất
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={start_time}&to={end_time}&symbol={ticker}&resolution=15"
    
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5).json()
        if 'c' not in res or len(res['c']) < 5: 
            return "⚠️ API Intraday từ chối trả kết quả. Bỏ qua quét phân phối ngầm."
            
        df = pd.DataFrame({'Close': res['c'], 'Volume': res['v']})
        
        # Đếm Volume của các nến xả (Giá giảm) vs Nến gom (Giá tăng)
        df['is_down'] = df['Close'] < df['Close'].shift(1)
        down_vol = df[df['is_down']]['Volume'].sum()
        up_vol = df[~df['is_down']]['Volume'].sum()
        
        if down_vol > (up_vol * 1.5):
            return "❌ CẢNH BÁO: Lực BÁN CHỦ ĐỘNG trong phiên áp đảo. Rủi ro Bull-Trap (Kéo xả)."
        elif up_vol > (down_vol * 1.2):
            return "✅ Lực CẦU GOM HÀNG chủ động trong phiên rất tốt."
        else:
            return "⏸️ Cung cầu trong phiên giằng co, chưa có dấu hiệu phân phối."
            
    except Exception:
        return "⚠️ Đứt kết nối API Intraday. Tạm bỏ qua."

def run_deep_scan(top_tickers_dict):
    """
    Hàm Tổng Tư Lệnh: Nhận danh sách Top 5 từ Markowitz, trả về kết luận X-Quang.
    """
    if not top_tickers_dict:
        return "Không có mã nào trong Bảng Lệnh để soi nội tại."
        
    print(f"\n🕵️ [TRẠM KIỂM ĐỊNH ALPHA VANTAGE (VN-VER)] Bắt đầu soi BCTC cho {len(top_tickers_dict)} mã...")
    
    report_lines = []
    for ticker in top_tickers_dict.keys():
        print(f"   => Đang chụp X-Quang mã {ticker}...")
        
        # Chạy 2 lớp quét
        cf_status = check_cash_flow_tcbs(ticker)
        intra_status = check_intraday_distribution(ticker)
        
        # Tòa tuyên án: Chỉ cần 1 lỗi ĐỎ là dính Án Tử
        if "❌" in cf_status or "❌" in intra_status:
            verdict = "🚨 NGUY HIỂM - ĐỀ NGHỊ HỦY LỆNH"
        else:
            verdict = "🛡️ NỘI TẠI AN TOÀN - DUYỆT"
            
        report_lines.append(f"**[{ticker}] {verdict}**\n  - BCTC (Dòng tiền): {cf_status}\n  - Intraday (15m): {intra_status}\n")
        
        time.sleep(1) # Nghỉ 1 nhịp nhẹ nhàng, không cần 15s vì API nội địa rất thoáng
        
    return "\n".join(report_lines)
