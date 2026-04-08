import pandas as pd
import numpy as np
import google.generativeai as genai
import requests
import time
import os
import yfinance as yf
from datetime import datetime, timedelta
import math
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & API
# ==========================================
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❌ LỖI: Chưa cấu hình GEMINI_API_KEY trong Environment Variables.")
    exit(1)
genai.configure(api_key=API_KEY)

# LẤY TỪ .ENV HOẶC GITHUB SECRETS
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

EMAIL_USER = os.environ.get("EMAIL_USER", "") 
EMAIL_PASS = os.environ.get("EMAIL_PASS", "")

# Đã nâng cấp: Cấu trúc danh sách nhiều Email nhận
RECEIVER_EMAILS = [
    "tranbaotrung2703@gmail.com",
    "trung.tran@saigontel.vn"
]

# ==========================================
# 2. CÁC HÀM LẤY DỮ LIỆU CÓ CƠ CHẾ RETRY & KIỂM TRA LỖI
# ==========================================
def get_ohlcv_data(ticker, days=150, max_retries=3):
    """Lấy dữ liệu OHLCV với cơ chế Thử lại (Retry) và Rào chắn Rác (Garbage Check)"""
    end_time = int(time.time())
    start_time = int((datetime.now() - timedelta(days=days * 1.8)).timestamp())
    
    # ĐÃ SỬA: Loại E1VFVN30 ra khỏi list Index để API hiểu nó là Stock
    asset_type = "index" if ticker in ["VNINDEX", "VN30", "HNX", "UPCOM"] else "stock"
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{asset_type}?from={start_time}&to={end_time}&symbol={ticker}&resolution=1D"
    
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            data = res.json()
            
            if 'c' in data and len(data['c']) > 0:
                df = pd.DataFrame({
                    'Date': pd.to_datetime(data['t'], unit='s'),
                    'Open': np.array(data['o'], dtype=float),
                    'High': np.array(data['h'], dtype=float),
                    'Low': np.array(data['l'], dtype=float),
                    'Close': np.array(data['c'], dtype=float),
                    'Volume': np.array(data['v'], dtype=float)
                })
                df.set_index('Date', inplace=True)
                
                # RÀO CHẮN 1: TỰ ĐỘNG HỦY NẾU DỮ LIỆU LỖI (GIÁ <= 0 HOẶC RỖNG)
                if df.empty or (df['Close'] <= 0).any() or (df['High'] <= 0).any() or (df['Volume'] < 0).any():
                    print(f"⚠️ [LỖI DỮ LIỆU] {ticker}: Dữ liệu trả về có chứa giá trị 0 hoặc âm. Cắt bỏ mã này.")
                    return None 
                
                return df.tail(days)
            else:
                print(f"⚠️ API trả về rỗng cho {ticker}. Thử lại {attempt+1}/{max_retries}...")
        except Exception as e:
            print(f"⚠️ Lỗi kết nối {ticker} ({type(e).__name__}). Thử lại {attempt+1}/{max_retries}...")
            
        time.sleep(2) # Nghỉ 2 giây trước khi thử lại theo đúng SOP
        
    return None # Thất bại hoàn toàn sau 3 lần thử

def get_fundamentals(ticker):
    if ticker in ["VNINDEX", "VN30", "HNX", "UPCOM", "E1VFVN30"]: return np.nan, np.nan
    try:
        yf_ticker = yf.Ticker(f"{ticker}.VN")
        info = yf_ticker.info
        pe, roe = info.get('trailingPE', np.nan), info.get('returnOnEquity', np.nan)
        return round(pe, 2) if pd.notna(pe) else np.nan, round(roe * 100, 2) if pd.notna(roe) else np.nan
    except: return np.nan, np.nan

def calculate_rrg_and_drawdown(stock_prices, benchmark_prices):
    if len(stock_prices) < 20 or len(benchmark_prices) < 20: return np.nan, np.nan, "N/A", np.nan
    min_len = min(len(stock_prices), len(benchmark_prices))
    
    # Lấy dữ liệu với độ dài bằng nhau
    s_prices = stock_prices.iloc[-min_len:]
    b_prices = benchmark_prices.iloc[-min_len:]
    
    # Tính Relative Strength
    rs = (s_prices.values / b_prices.values) * 100
    rs_series = pd.Series(rs)
    rs_ma10 = rs_series.rolling(window=10).mean()
    
    # Chuẩn hóa cách gọi phần tử cuối bằng .iloc[-1] thay vì [-1]
    if pd.isna(rs_ma10.iloc[-1]) or pd.isna(rs_ma10.iloc[-2]): return np.nan, np.nan, "N/A", np.nan
    
    rs_ratio_current = (rs_series.iloc[-1] / rs_ma10.iloc[-1]) * 100
    rs_ratio_prev = (rs_series.iloc[-2] / rs_ma10.iloc[-2]) * 100
    rs_mom = (rs_ratio_current / rs_ratio_prev) * 100
    
    # Xác định Góc phần tư
    quad = "Leading" if rs_ratio_current > 100 and rs_mom > 100 else "Weakening" if rs_ratio_current > 100 else "Improving" if rs_mom > 100 else "Lagging"
    
    # Tính Max Drawdown
    peaks = s_prices.cummax()
    drawdowns = (s_prices - peaks) / peaks
    mdd = drawdowns.min() * 100
    
    return round(rs_ratio_current, 2), round(rs_mom, 2), quad, round(mdd, 2)

def optimize_portfolio_monte_carlo(raw_price_dict, ticker_caps):
    df = pd.DataFrame(raw_price_dict)
    returns = df.pct_change().dropna()
    num_assets = len(df.columns)
    
    results, weights_record = np.zeros((3, 2000)), []
    mean_ret, cov_mat = returns.mean() * 252, returns.cov() * 252
    
    for i in range(2000):
        w = np.random.random(num_assets)
        w /= np.sum(w)
        # Ép trần tỷ trọng từng mã (Cap Weight)
        for j, ticker in enumerate(df.columns):
            cap = ticker_caps.get(ticker, 0.4) # Mặc định tối đa 40% nếu không cấu hình
            if w[j] > cap: w[j] = cap
        
        # Tái chuẩn hóa sau khi ép trần
        w /= np.sum(w)
        weights_record.append(w)
        results[0,i] = np.sum(mean_ret * w)
        results[1,i] = np.sqrt(np.dot(w.T, np.dot(cov_mat, w)))
        results[2,i] = results[0,i] / results[1,i]
        
    opt_w = weights_record[np.argmax(results[2])]
    return {df.columns[i]: round(opt_w[i]*100, 2) for i in range(num_assets)}

def extract_micro_timing_insights(df, ticker, lookback=20, bins=50):
    if df is None or len(df) < lookback: return f"- {ticker}: Không đủ dữ liệu.", df['Close'].iloc[-1], 0
    cp = df['Close'].iloc[-1]
    
    # 1. TÍNH ATR 14 NGÀY (Biến động thực tế)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    atr = np.max(ranges, axis=1).rolling(14).mean().iloc[-1]
    if pd.isna(atr) or atr == 0: atr = cp * 0.02 # Dự phòng 2% nếu lỗi
    
    # 2. TÍNH LOCAL POC (Nền giá 30 ngày gần nhất)
    df_local = df.tail(30)
    price_bins = np.linspace(df_local['Low'].min(), df_local['High'].max(), bins)
    vp_data = [{'Price': (price_bins[i] + price_bins[i+1])/2, 'Vol': df_local.loc[(df_local['Close'] >= price_bins[i]) & (df_local['Close'] < price_bins[i+1]), 'Volume'].sum()} for i in range(len(price_bins)-1)]
    local_poc = pd.DataFrame(vp_data).loc[pd.DataFrame(vp_data)['Vol'].idxmax(), 'Price'] if vp_data else cp

    df['Sup'], df['Res'] = df['Low'].rolling(lookback).min().shift(1), df['High'].rolling(lookback).max().shift(1)
    df['Avg_Vol'] = df['Volume'].rolling(lookback).mean()
    
    df['Spring'] = (df['Low'] < df['Sup']) & (df['Close'] > (df['High'] + df['Low']) / 2) & (df['Volume'] > df['Avg_Vol'])
    df['UTAD'] = (df['High'] > df['Res']) & (df['Close'] < (df['High'] + df['Low']) / 2) & (df['Volume'] > df['Avg_Vol'])
    df['SOS'] = (df['Close'] > df['Res']) & (df['Close'] > df['Open']) & (df['Volume'] > df['Avg_Vol'] * 1.5)

    recent_vol_trend = df['Volume'].tail(10).mean() / df['Volume'].tail(30).mean()
    phase_est = "Pha B"
    if recent_vol_trend < 0.7: phase_est = "Pha B cạn cung"
    elif cp > df['Res'].iloc[-1] and recent_vol_trend > 1.2: phase_est = "Pha D/E (Đẩy)"
    elif cp < df['Sup'].iloc[-1] and recent_vol_trend > 1.2: phase_est = "Pha A (Rơi)"

    recent = df.tail(5)
    w_event = "Đi ngang"
    if recent['Spring'].any(): w_event = f"SPRING tại {recent[recent['Spring']]['Low'].iloc[-1]:.2f}"
    elif recent['UTAD'].any(): w_event = f"UTAD tại {recent[recent['UTAD']]['High'].iloc[-1]:.2f}"
    elif recent['SOS'].any(): w_event = "SOS Xác nhận"

    return f"- {ticker}: Giá {cp:.2f} | Local POC {local_poc:.2f} | ATR {atr:.2f} | {phase_est} | {w_event}", local_poc, atr

# ==========================================
# 3. CÁC HÀM CÀO DỮ LIỆU VĨ MÔ & EMAIL
# ==========================================
def get_macro_quant():
    # Thêm VIX vào danh sách cào dữ liệu
    tickers = {"DXY (Chỉ số USD)": "DX-Y.NYB", "US10Y (Lợi suất TP Mỹ)": "^TNX", "Crude Oil (Dầu thô)": "CL=F", "Gold (Vàng)": "GC=F", "VIX (Chỉ số Sợ hãi)": "^VIX"}
    macro_data = {}
    for name, sym in tickers.items():
        try:
            hist = yf.Ticker(sym).history(period="1mo")
            if not hist.empty:
                s, e = hist['Close'].iloc[0], hist['Close'].iloc[-1]
                macro_data[name] = {"Mức hiện tại": round(e, 2), "Biến động 1T (%)": round(((e - s)/s)*100, 2)}
        except: macro_data[name] = {"Mức hiện tại": "N/A", "Biến động 1T (%)": "N/A"}
    return pd.DataFrame(macro_data).T

def agentic_web_search(query):
    if not query.strip(): return ""
    out_text = ""
    # Lớp 1: Ưu tiên Tavily (AI Search Agent)
    if TAVILY_API_KEY:
        try:
            res = requests.post("https://api.tavily.com/search", json={"api_key": TAVILY_API_KEY, "query": query, "max_results": 3}, timeout=10)
            if res.status_code == 200:
                out = [f"- [{item['title']}] {item['content']}" for item in res.json().get('results', [])]
                return "🔍 [Tavily API]\n" + "\n".join(out)
        except: pass
    # Lớp 2: Dự phòng DuckDuckGo Lite
    try:
        res = DDGS().text(query, max_results=3, backend="lite")
        return "🔍 [DuckDuckGo]\n" + "\n".join([f"- [{r.get('title')}] {r.get('body')}" for r in res]) if res else ""
    except: return "❌ Lỗi toàn bộ Web Search"

import markdown # Thêm dòng này ở đầu file cùng các lệnh import khác

def send_email(subject, body):
    """Hàm gửi báo cáo V33 hiển thị trực tiếp nội dung đẹp trên nhiều Email"""
    if not EMAIL_USER or not EMAIL_PASS:
        print("⚠️ Bỏ qua gửi Email vì chưa cấu hình tài khoản.")
        return
        
    html_content = markdown.markdown(body, extensions=['tables', 'fenced_code'])
    
    email_style = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
        h1, h2, h3 { color: #1a73e8; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; background-color: #f8f9fa; }
        th, td { border: 1px solid #dee2e6; padding: 12px; text-align: left; }
        th { background-color: #1a73e8; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .footer { font-size: 0.8em; color: #777; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
    """
    
    final_html = f"""
    <html>
    <head>{email_style}</head>
    <body>
        <div style="max-width: 800px; margin: auto;">
            {html_content}
            <div class="footer">
                <p>Báo cáo này được tạo tự động bởi Hệ thống <b>Quant 3D Matrix V33</b>.</p>
                <p>Thời gian thực thi: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_USER
    
    # ĐÃ SỬA: Gộp danh sách email thành chuỗi cách nhau bằng dấu phẩy
    msg['To'] = ", ".join(RECEIVER_EMAILS)
    
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    msg.attach(MIMEText(final_html, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        # ĐÃ SỬA: Báo cáo số lượng email gửi thành công
        print(f"📧 [THÀNH CÔNG] Báo cáo V33 đã được gửi đến {len(RECEIVER_EMAILS)} địa chỉ email.")
    except Exception as e:
        print(f"❌ Lỗi gửi Email: {str(e)}")

# ==========================================
# 4. BỘ NÃO TỰ ĐẢO MODEL (FALLBACK AI)
# ==========================================
def generate_ai_report_with_fallback(prompt):
    # CẬP NHẬT DANH SÁCH BĂNG ĐẠN MODEL (TỪ MỚI NHẤT ĐẾN CŨ NHẤT)
    fallback_models = [
        "gemini-3.1-pro",          # Ưu tiên 1: Dòng Pro thông minh nhất (Sẽ tự skip nếu quota 0/0)
        "gemini-3.1-flash-lite",   # Ưu tiên 2: Dòng Flash Lite mới nhất, phản hồi siêu tốc
        "gemini-3.0-flash",        # Ưu tiên 3: Tương ứng với Gemini 3 Flash trên Dashboard
        "gemini-3-flash",          # (Mã dự phòng alias cho bản 3.0)
        "gemini-2.5-flash",        # Ưu tiên 4: Bản 2.5 cực kỳ ổn định và thông minh
        "gemini-2.5-flash-lite",   # Ưu tiên 5: Bản nhẹ của 2.5
        "gemini-1.5-pro",          # Cứu cánh 1: Khi toàn bộ dòng 2 và 3 sập mạng
        "gemini-1.5-flash"         # Cứu cánh 2: Trâu bò nhất, dùng để vét đáy
    ]
    
    for model_name in fallback_models:
        try:
            print(f"🤖 Kích hoạt não bộ: [{model_name}]...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"✅ THÀNH CÔNG từ [{model_name}]")
            return response.text
        except Exception as e:
            # IN RA MÃ LỖI GỐC ĐỂ BÁT BỆNH (Vd: 403 Quota, 404 Not Found...)
            print(f"⚠️ Model [{model_name}] thất bại. Lỗi: {str(e)}")
            time.sleep(1) # Nghỉ 1 giây rồi đổi súng bắn tiếp
            continue
            
    return "❌ LỖI NGHIÊM TRỌNG: Toàn bộ băng đạn Model đều đã thử và thất bại. Hãy kiểm tra Terminal để đọc mã lỗi gốc!"

# ==========================================
# 5. LUỒNG THỰC THI CHÍNH (MAIN AGENT LOOP)
# ==========================================
def run_quant_agent(tickers_input, macro_query):
    # Lấy ngày hiện tại chuẩn từ hệ thống máy tính
    today_str = datetime.now().strftime('%d/%m/%Y')
    print("\n=========================================")
    print(f"🚀 KHỞI ĐỘNG AGENT QUANT TRADING (V33) LÚC {datetime.now().strftime('%H:%M:%S')}")
    print("=========================================\n")
    
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    time_window, max_weight_limit = 150, 40
    
    # Kéo Market Pulse (Dùng E1VFVN30)
    df_pulse = get_ohlcv_data("E1VFVN30", days=40, max_retries=3)
    if df_pulse is None:
        error_msg = "❌ TỰ HỦY: Lỗi API lấy dữ liệu E1VFVN30 (Proxy Dòng tiền). Hệ thống dừng để bảo toàn an toàn."
        print(error_msg); send_email("[BÁO ĐỘNG LỖI] Quant V33", error_msg); return
        
    deviation = ((df_pulse['Close'].iloc[-1] - df_pulse['Close'].tail(20).mean()) / df_pulse['Close'].tail(20).mean()) * 100
    market_status = f"GREED (+{deviation:.2f}%)" if deviation > 1.0 else f"FEAR ({deviation:.2f}%)" if deviation < -1.0 else f"NEUTRAL ({deviation:.2f}%)"
    
    df_bench = get_ohlcv_data("VNINDEX", days=time_window, max_retries=3)
    if df_bench is None:
        error_msg = "❌ TỰ HỦY: Lỗi API lấy dữ liệu VNINDEX. Hệ thống dừng để bảo toàn an toàn."
        print(error_msg); send_email("[BÁO ĐỘNG LỖI] Quant V33", error_msg); return
    bench_prices = df_bench['Close']
    
    print(f"⏳ [1/4] Cào & Lọc Thanh khoản cho {len(tickers)} mã...")
    data_list, raw_price_dict, micro_insights = [], {}, []
    ticker_caps = {}  # <--- BƯỚC 1: BỔ SUNG DÒNG KHOẢNG TRẮNG NÀY Ở ĐÂY
    
    for t in tickers:
        df_ohlcv = get_ohlcv_data(t, days=time_window, max_retries=3)
        if df_ohlcv is None: continue # Skip nếu API lỗi sau 3 lần retry
        
        # ==========================================
        # KHỐI PHÂN TÍCH VSA & CẠN CUNG (VERSION 33)
        # ==========================================
        # 1. Tính toán Tiền & Trung bình lịch sử
        df_ohlcv['Gia_Tri_GD'] = df_ohlcv['Close'] * df_ohlcv['Volume'] * 1000  # Nhân 1000 vì giá của ENTRADE thường chia ngàn
        df_ohlcv['Vol_MA20'] = df_ohlcv['Gia_Tri_GD'].rolling(window=20).mean()

        # 2. LỚP LỌC 1: CHẶN PENNY RÁC (Trung bình 20 phiên phải >= 50 tỷ)
        avg_20d_val = df_ohlcv['Vol_MA20'].iloc[-1]
        if pd.isna(avg_20d_val) or avg_20d_val < 50_000_000_000:
            print(f"⏭️ Bỏ qua {t}: Thanh khoản trung bình 20 phiên không đạt chuẩn (< 50 tỷ).")
            continue

        # 3. LỚP LỌC 2: PHÁT HIỆN CẠN CUNG TỪNG PHIÊN (VSA No Supply Bar)
        df_ohlcv['Price_Range'] = (df_ohlcv['High'] - df_ohlcv['Low']) / df_ohlcv['Close']
        df_ohlcv['is_low_vol'] = df_ohlcv['Gia_Tri_GD'] < (df_ohlcv['Vol_MA20'] * 0.6)
        df_ohlcv['is_tight_price'] = df_ohlcv['Price_Range'] < (df_ohlcv['Price_Range'].rolling(20).mean() * 0.8)
        
        # Sửa lỗi NaN cho MA50 bằng cách lấp đầy dữ liệu thiếu
        df_ohlcv['MA50'] = df_ohlcv['Close'].rolling(50).mean().bfill()
        df_ohlcv['is_above_trend'] = df_ohlcv['Close'] > df_ohlcv['MA50']

        df_ohlcv['Can_Cung_Daily'] = df_ohlcv['is_low_vol'] & df_ohlcv['is_tight_price'] & df_ohlcv['is_above_trend']

        # 4. XÁC THỰC CỤM LỊCH SỬ (CLUSTER VALIDATION) - Kiểm tra 5 phiên gần nhất
        df_ohlcv['Can_Cung_Cluster'] = df_ohlcv['Can_Cung_Daily'].rolling(window=5).sum()

       # 5. LẤY BIẾN SỐ VSA & ĐO KHOẢNG CÁCH ATR
        insight_text, local_poc, atr = extract_micro_timing_insights(df_ohlcv, t)
        current_price = df_ohlcv['Close'].iloc[-1]
        
        distance_from_poc = abs(current_price - local_poc)
        atr_boundary = atr * 1.5  # Chấp nhận sai số dao động 1.5 lần ATR quanh POC
        
        latest_status = df_ohlcv.iloc[-1]
        vsa_signal_text = "Thanh khoản ở mức bình thường."
        
        if latest_status['Can_Cung_Daily'] == True and latest_status['Can_Cung_Cluster'] >= 2:
            if distance_from_poc <= atr_boundary:
                vsa_signal_text = "🔥 VSA KHẨN CẤP (CẠN CUNG): Lực bán kiệt quệ quanh nền Local POC. Điểm mua tuyệt vời."
            elif (current_price - local_poc) > (atr * 3):
                vsa_signal_text = "⚠️ BÁO ĐỘNG ĐỎ (THIẾU CẦU): Giá kéo quá xa nền POC nhưng Volume tắt lịm. CẤM MUA ĐUỔI."
            else:
                vsa_signal_text = "⚡ VSA TIỀM NĂNG: Thanh khoản cạn nhưng nền giá hơi lỏng."

        # 6. THIẾT LẬP TRẦN TỶ TRỌNG (CAP WEIGHT) CHỐNG ĐU ĐỈNH
        # (Đã xóa dòng if t not in...)
        if (current_price - local_poc) > (atr * 3):
            ticker_caps[t] = 0.05  # Phạt trần tỷ trọng tối đa chỉ 5%
        else:
            ticker_caps[t] = max_weight_limit / 100.0  # Bình thường cho phép Max Weight

        pe, roe = get_fundamentals(t)
        prices = df_ohlcv['Close']
        raw_price_dict[t] = prices
        micro_insights.append(insight_text)
        x, y, quad, mdd = calculate_rrg_and_drawdown(prices, bench_prices)
        
        data_list.append({
            "Mã": t, 
            "Giá Hiện Tại": round(current_price, 2), 
            "Vị thế RRG": quad, 
            "Vùng Mua POC": round(local_poc, 2), # Cập nhật hiển thị Local POC
            "Tín hiệu VSA": vsa_signal_text,
            "P/E": pe, 
            "ROE (%)": roe, 
            "Max DD (%)": mdd,
            "RRG_X": x, 
            "RRG_Y": y
        })
        time.sleep(0.5)

    # RÀO CHẮN 3: KIỂM TRA SỐ LƯỢNG MÃ CÒN LẠI SAU KHI LỌC
    if len(data_list) < 3:
        error_msg = "❌ TỰ HỦY: Số lượng mã đạt chuẩn thanh khoản (< 3 mã) không đủ để thuật toán Markowitz chạy tối ưu hóa danh mục."
        print(error_msg); send_email("[CẢNH BÁO BỎ QUA BƯỚC 2] Quant V33", error_msg); return

    df_quant = pd.DataFrame(data_list)
    print("⏳ [2/4] Chạy Toán học Markowitz...")
    opt_weights = optimize_portfolio_monte_carlo(raw_price_dict, max_weight_limit)

    print("⏳ [3/4] Quét Bảng điện Vĩ mô...")
    df_macro = get_macro_quant()
    search_res = agentic_web_search(macro_query)
    
    print("⏳ [4/4] Tổng hợp dữ liệu & Kích hoạt AI viết báo cáo...")
    
    # Lấy ngày hiện tại chuẩn từ hệ thống Python
    today_str = datetime.now().strftime('%d/%m/%Y')

    master_prompt = f"""
    ĐÓNG VAI: GIÁM ĐỐC QUẢN TRỊ RỦI RO QUỸ ĐẦU TƯ (HỆ THỐNG 3D MATRIX)
    THỜI GIAN THỰC TẾ HÔM NAY LÀ: {datetime.now().strftime('%Y-%m-%d')}
    
    [CHIỀU 1: LƯỢNG TỬ MARKOWITZ & VSA]
    - Tín hiệu Dòng tiền: {market_status}
    - Bảng Cơ bản, RRG, Local POC & VSA: {df_quant.to_string()}
    - Tỷ trọng Giải ngân Markowitz (Đã ép trần chống đu đỉnh): {opt_weights}
    
    [CHIỀU 2: MICRO-TIMING WYCKOFF]
    {chr(10).join(micro_insights)}
    
    [CHIỀU 3: CẦU DAO VĨ MÔ QUỐC TẾ & CHỈ SỐ VIX]
    - Vĩ mô 1 tháng qua: {df_macro.to_string()}
    - Tin tức AI cào được: {search_res}
    
    * LUẬT ĐÁNH GIÁ VĨ MÔ NGHỊCH LÝ (BẮT BUỘC TUÂN THỦ):
    - KHÔNG kết luận Vĩ mô tốt/xấu chỉ bằng tin tức (như Thất nghiệp, Suy thoái). Phải dùng Toán học:
    - Nếu Tin xấu + Lợi suất US10Y GIẢM + VIX < 25: Đây là TIN TỐT (Kỳ vọng FED bơm tiền). Vĩ mô: TÍCH CỰC.
    - Nếu Tin xấu + Lợi suất US10Y GIẢM + VIX BÙNG NỔ (> 25): Đây là ĐỨT GÃY TÍN DỤNG. Vĩ mô: CỰC KỲ XẤU. Bán tháo mọi thứ.
    
    NHIỆM VỤ: Trình bày Báo cáo Dành cho Trader dưới dạng Markdown.
    
    1. TỔNG QUAN VĨ MÔ & THỊ TRƯỜNG: Đánh giá theo đúng "Luật Đánh Giá Vĩ Mô Nghịch Lý". Chốt: Rủi ro Cao/Thấp?
    
    2. BẢNG LỆNH GIẢI NGÂN THỰC CHIẾN:
    Tạo 1 bảng gộp 3-5 mã tốt nhất. 
    * LUẬT ĐỊNH GIÁ: Vùng Giá Mua phải là "Giá Hiện Tại". Mức giá ở cột 'Vùng Mua POC' đóng vai trò là "Target Chốt Lời" (nếu POC > Giá) HOẶC "Hỗ trợ cắt lỗ" (nếu POC < Giá).
    * Các cột bắt buộc: Mã | Tỷ trọng Mới (%) | Vùng Mua (Giá Hiện Tại) | Target POC (Số POC) | Tín hiệu | Lý do.
    * LUẬT LOẠI BỎ: TUYỆT ĐỐI KHÔNG giải ngân vào các mã có Tín hiệu VSA là "BÁO ĐỘNG ĐỎ (THIẾU CẦU)".
    
    3. CẢNH BÁO RỦI RO ĐỎ: Gọi tên mã bị Thiếu Cầu vùng đỉnh, thủng đáy, dính UTAD, hoặc ROE quá thấp. Khuyến nghị HỦY LỆNH.
    
    4. LỆNH ĐIỀU ĐỘNG TỪ GIÁM ĐỐC QUỸ: Kết luận dứt khoát 3 dòng.
    * LUẬT TÍNH TIỀN MẶT BẮT BUỘC: % Tiền mặt = 100% - (Tổng % các mã ở Mục 2). BẮT BUỘC thực hiện tính toán và in kết quả.
    * Đưa ra hướng dẫn đặt lệnh (Vd: Mua ngay tại Giá Hiện Tại với Target tại POC).
    """
    
    final_report = generate_ai_report_with_fallback(master_prompt)
    
    print("\n=========================================")
    print("📑 BÁO CÁO NỘI TẠI (AGENT SKILL V33)")
    print("=========================================\n")
    print(final_report)
    print("\n=========================================")
    
    # GỬI EMAIL CHỐT HẠ
    email_subject = f"[Quant 3D Matrix] Lệnh Điều Động Vốn Ngày {today_str}"
    send_email(email_subject, final_report)
    
    return final_report

if __name__ == "__main__":
    # GỘP 48 MÃ TỪ CẨM NANG V33
    FULL_WATCHLIST = "VCB, BID, CTG, TCB, MBB, SSI, VND, VHM, VIC, VRE, HPG, HSG, PVD, PVS, DGC, DCM, DPM, VHC, ANV, PTB, MWG, PNJ, FPT, REE, GAS, NT2, VSH, VNM, SAB, KBC, SZC, IDC, VGC, DIG, NVL, PDR, DXG, KDH, NKG, VGS, SMC, VCI, HCM, SIP, DTD, NTC, PHR, GVR"
    
    # BỘ TỪ KHÓA VĨ MÔ TỐI ƯU (Tránh lỗi API và Tràn Token)
    # Dùng cú pháp nhóm (A và B) để AI Search tự động tổng hợp bức tranh toàn cảnh
    MACRO_KEYWORDS = "Tổng hợp tin tức Vĩ mô Việt Nam (Lãi suất, Tỷ giá, Đầu tư công) VÀ Điểm nóng kinh tế, rủi ro địa chính trị thế giới mới nhất hôm nay"
    
    run_quant_agent(FULL_WATCHLIST, MACRO_KEYWORDS)
