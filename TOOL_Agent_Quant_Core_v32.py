# ==========================================
# KHAI BÁO THƯ VIỆN (CHUẨN PEP 8)
# ==========================================

# 1. Thư viện hệ thống Python
import os
import time
import math
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 2. Thư viện bên thứ 3 (Third-party)
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import google.generativeai as genai
import markdown
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

# 3. Thư viện nội bộ (Local Modules)
from TOOL_DeepScan_Fundamentals import run_deep_scan, pre_screen_hard_cutoff

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & API
# ==========================================
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❌ LỖI: Chưa cấu hình GEMINI_API_KEY trong Environment Variables.")
    exit(1)
genai.configure(api_key=API_KEY)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASS = os.environ.get("EMAIL_PASS", "")

# Cấu trúc danh sách nhiều Email nhận
RECEIVER_EMAILS = [
    "tranbaotrung2703@gmail.com"
]

# ==========================================
# 2. CÁC HÀM LẤY DỮ LIỆU CÓ CƠ CHẾ RETRY & KIỂM TRA LỖI
# ==========================================
def get_ohlcv_data(ticker, days=150, max_retries=3):
    """Lấy dữ liệu OHLCV với cơ chế Thử lại (Retry) và Rào chắn Rác (Garbage Check)"""
    end_time = int(time.time())
    start_time = int((datetime.now() - timedelta(days=days * 1.8)).timestamp())

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

                if df.empty or (df['Close'] <= 0).any() or (df['High'] <= 0).any() or (df['Volume'] < 0).any():
                    print(f"⚠️ [LỖI DỮ LIỆU] {ticker}: Dữ liệu trả về có chứa giá trị 0 hoặc âm. Cắt bỏ mã này.")
                    return None

                return df.tail(days)
            else:
                print(f"⚠️ API trả về rỗng cho {ticker}. Thử lại {attempt+1}/{max_retries}...")
        except Exception as e:
            print(f"⚠️ Lỗi kết nối {ticker} ({type(e).__name__}). Thử lại {attempt+1}/{max_retries}...")

        time.sleep(2)

    return None

def get_fundamentals(ticker):
    if ticker in ["VNINDEX", "VN30", "HNX", "UPCOM", "E1VFVN30"]:
        return np.nan, np.nan
    try:
        yf_ticker = yf.Ticker(f"{ticker}.VN")
        info = yf_ticker.info
        pe, roe = info.get('trailingPE', np.nan), info.get('returnOnEquity', np.nan)
        return round(pe, 2) if pd.notna(pe) else np.nan, round(roe * 100, 2) if pd.notna(roe) else np.nan
    except:
        return np.nan, np.nan

def calculate_rrg_and_drawdown(stock_prices, benchmark_prices):
    if len(stock_prices) < 20 or len(benchmark_prices) < 20:
        return np.nan, np.nan, "N/A", np.nan
    min_len = min(len(stock_prices), len(benchmark_prices))

    s_prices = stock_prices.iloc[-min_len:]
    b_prices = benchmark_prices.iloc[-min_len:]

    rs = (s_prices.values / b_prices.values) * 100
    rs_series = pd.Series(rs)
    rs_ma10 = rs_series.rolling(window=10).mean()

    if pd.isna(rs_ma10.iloc[-1]) or pd.isna(rs_ma10.iloc[-2]):
        return np.nan, np.nan, "N/A", np.nan

    rs_ratio_current = (rs_series.iloc[-1] / rs_ma10.iloc[-1]) * 100
    rs_ratio_prev = (rs_series.iloc[-2] / rs_ma10.iloc[-2]) * 100
    rs_mom = (rs_ratio_current / rs_ratio_prev) * 100

    quad = "Leading" if rs_ratio_current > 100 and rs_mom > 100 else "Weakening" if rs_ratio_current > 100 else "Improving" if rs_mom > 100 else "Lagging"

    peaks = s_prices.cummax()
    drawdowns = (s_prices - peaks) / peaks
    mdd = drawdowns.min() * 100

    return round(rs_ratio_current, 2), round(rs_mom, 2), quad, round(mdd, 2)

def calculate_market_regime_and_cash_ratio(df_macro, leading_count: int = 0):
    """
    [NÂNG CẤP V33] QUY TẮC THÍCH ỨNG TỶ TRỌNG TIỀN MẶT (DYNAMIC CASH BUFFER):
    Tự động phân tầng tỷ trọng dựa trên biến động của DXY, US10Y và nhóm ngành dẫn dắt.
    """
    try:
        dxy_chg = float(df_macro.loc["DXY (Chỉ số USD)", "Biến động 1T (%)"])
        us10y_chg = float(df_macro.loc["US10Y (Lợi suất TP Mỹ)", "Biến động 1T (%)"])
        us10y_val = float(df_macro.loc["US10Y (Lợi suất TP Mỹ)", "Mức hiện tại"])
        vix_val = float(df_macro.loc["VIX (Chỉ số Sợ hãi)", "Mức hiện tại"])
    except:
        dxy_chg, us10y_chg, us10y_val, vix_val = 0.0, 0.0, 5.0, 16.0

    # Điều kiện Vĩ mô hạ nhiệt: US10Y hoặc DXY tạo đỉnh/giảm trong tháng, VIX < 25
    is_macro_cooling = (us10y_chg < 0 or dxy_chg < 0 or us10y_val < 5.0) and vix_val < 25

    if is_macro_cooling and leading_count >= 2:
        regime = "SELECTIVE_EXPANSION"
        target_cash_ratio = 65.0      # 65% Tiền mặt
        target_allocation = 0.35      # Nới lỏng giải ngân 35% cho nhóm Leading
    elif us10y_val >= 5.2 or dxy_chg > 2.0:
        regime = "DEFENSIVE_HIGH_RISK"
        target_cash_ratio = 82.0      # 82% Tiền mặt
        target_allocation = 0.18      # Thu hẹp giải ngân 18% phòng thủ
    else:
        regime = "DEFENSIVE_MODERATE"
        target_cash_ratio = 78.0      # 78% Tiền mặt
        target_allocation = 0.22      # Giải ngân 22%

    return regime, target_cash_ratio, target_allocation

def optimize_portfolio_monte_carlo(raw_price_dict, ticker_caps, target_allocation=0.35):
    """
    [NÂNG CẤP V33] TỐI ƯU HÓA MARKOWITZ VỚI THUẬT TOÁN ÉP TRẦN CHUẨN XÁC:
    Áp dụng Iterative Proportional Fitting để chia lại phần tỷ trọng dôi dư,
    đảm bảo không mã nào vượt trần và tổng tỷ trọng đúng bằng target_allocation.
    """
    df = pd.DataFrame(raw_price_dict)
    returns = df.pct_change().dropna()
    num_assets = len(df.columns)

    if num_assets == 0:
        return {}

    # Nếu chỉ có 1 hoặc 2 mã, chia đều tỷ trọng trong trần an toàn
    if num_assets < 3:
        each_w = round((target_allocation / num_assets) * 100, 2)
        return {df.columns[i]: each_w for i in range(num_assets)}

    results = np.zeros((3, 2000))
    weights_record = []
    mean_ret = returns.mean() * 252
    cov_mat = returns.cov() * 252

    for i in range(2000):
        w = np.random.random(num_assets)
        w /= np.sum(w)
        weights_record.append(w)
        results[0, i] = np.sum(mean_ret * w)
        results[1, i] = np.sqrt(np.dot(w.T, np.dot(cov_mat, w)))
        results[2, i] = results[0, i] / results[1, i] if results[1, i] > 0 else 0

    best_raw_w = weights_record[np.argmax(results[2])]

    # Bước 1: Scale tỷ trọng thô theo mục tiêu giải ngân
    w_scaled = best_raw_w * target_allocation

    # Bước 2: Thuật toán ép trần phân bổ phần dư (Iterative Capping)
    caps_array = np.array([ticker_caps.get(col, 0.08) for col in df.columns])

    for _ in range(10):
        excess = 0.0
        free_indices = []
        for j in range(num_assets):
            if w_scaled[j] > caps_array[j]:
                excess += (w_scaled[j] - caps_array[j])
                w_scaled[j] = caps_array[j]
            elif w_scaled[j] < caps_array[j]:
                free_indices.append(j)

        if excess <= 1e-6 or not free_indices:
            break

        free_sum = sum(w_scaled[idx] for idx in free_indices)
        if free_sum > 0:
            for idx in free_indices:
                w_scaled[idx] += excess * (w_scaled[idx] / free_sum)
        else:
            for idx in free_indices:
                w_scaled[idx] += excess / len(free_indices)

    return {df.columns[i]: round(w_scaled[i] * 100, 2) for i in range(num_assets)}

def extract_micro_timing_insights(df, ticker, lookback=20, bins=50):
    if df is None or len(df) < lookback:
        return f"- {ticker}: Không đủ dữ liệu.", df['Close'].iloc[-1] if df is not None else 0, 0, False
    cp = df['Close'].iloc[-1]

    # 1. TÍNH ATR 14 NGÀY
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    atr = np.max(ranges, axis=1).rolling(14).mean().iloc[-1]
    if pd.isna(atr) or atr == 0:
        atr = cp * 0.02

    # 2. TÍNH LOCAL POC
    df_local = df.tail(30)
    price_bins = np.linspace(df_local['Low'].min(), df_local['High'].max(), bins)
    vp_data = [{'Price': (price_bins[i] + price_bins[i+1])/2, 'Vol': df_local.loc[(df_local['Close'] >= price_bins[i]) & (df_local['Close'] < price_bins[i+1]), 'Volume'].sum()} for i in range(len(price_bins)-1)]
    local_poc = pd.DataFrame(vp_data).loc[pd.DataFrame(vp_data)['Vol'].idxmax(), 'Price'] if vp_data else cp

    df['Sup'] = df['Low'].rolling(lookback).min().shift(1)
    df['Res'] = df['High'].rolling(lookback).max().shift(1)
    df['Avg_Vol'] = df['Volume'].rolling(lookback).mean()

    # Nhận diện tín hiệu Wyckoff
    df['Spring'] = (df['Low'] < df['Sup']) & (df['Close'] > (df['High'] + df['Low']) / 2) & (df['Volume'] < df['Avg_Vol'] * 1.1)
    df['UTAD'] = (df['High'] > df['Res']) & (df['Close'] < (df['High'] + df['Low']) / 2) & (df['Volume'] > df['Avg_Vol'])
    df['SOS'] = (df['Close'] > df['Res']) & (df['Close'] > df['Open']) & (df['Volume'] > df['Avg_Vol'] * 1.5)

    recent_vol_trend = df['Volume'].tail(10).mean() / df['Volume'].tail(30).mean()
    phase_est = "Pha B"
    if recent_vol_trend < 0.7:
        phase_est = "Pha B cạn cung"
    elif cp > df['Res'].iloc[-1] and recent_vol_trend > 1.2:
        phase_est = "Pha D/E (Đẩy)"
    elif cp < df['Sup'].iloc[-1] and recent_vol_trend > 1.2:
        phase_est = "Pha A (Rơi)"

    recent = df.tail(5)
    w_event = "Đi ngang"
    has_recent_utad = False

    if recent['Spring'].any():
        w_event = f"SPRING tại {recent[recent['Spring']]['Low'].iloc[-1]:.2f}"
    elif recent['UTAD'].any():
        w_event = f"UTAD tại {recent[recent['UTAD']]['High'].iloc[-1]:.2f}"
        has_recent_utad = True
    elif recent['SOS'].any():
        w_event = "SOS Xác nhận"

    return f"- {ticker}: Giá {cp:.2f} | Local POC {local_poc:.2f} | ATR {atr:.2f} | {phase_est} | {w_event}", local_poc, atr, has_recent_utad

# ==========================================
# 3. CÁC HÀM CÀO DỮ LIỆU VĨ MÔ & EMAIL
# ==========================================
def get_macro_quant():
    tickers = {"DXY (Chỉ số USD)": "DX-Y.NYB", "US10Y (Lợi suất TP Mỹ)": "^TNX", "Crude Oil (Dầu thô)": "CL=F", "Gold (Vàng)": "GC=F", "VIX (Chỉ số Sợ hãi)": "^VIX"}
    macro_data = {}
    for name, sym in tickers.items():
        try:
            hist = yf.Ticker(sym).history(period="1mo")
            if not hist.empty:
                s, e = hist['Close'].iloc[0], hist['Close'].iloc[-1]
                macro_data[name] = {"Mức hiện tại": round(e, 2), "Biến động 1T (%)": round(((e - s)/s)*100, 2)}
        except:
            macro_data[name] = {"Mức hiện tại": "N/A", "Biến động 1T (%)": "N/A"}
    return pd.DataFrame(macro_data).T
    
def get_vn_interest_rates():
    """
    Quét kép mặt bằng lãi suất chuẩn Việt Nam:
    1. Biến động hàng ngày: Lãi suất liên ngân hàng qua đêm & OMO của NHNN (nhảy số mỗi ngày).
    2. Mặt bằng chuẩn: Lãi suất tiết kiệm 12 tháng & cho vay nhóm Big4 (VCB, BIDV, VietinBank, Agribank).
    """
    q_interbank = "Lãi suất liên ngân hàng qua đêm NHNN và bơm hút ròng OMO tín phiếu mới nhất hôm nay"
    q_big4 = "Lãi suất tiết kiệm huy động 12 tháng và lãi suất cho vay nhóm Big4 Vietcombank BIDV VietinBank mới nhất"
    
    res_interbank = agentic_web_search(q_interbank)
    res_big4 = agentic_web_search(q_big4)
    
    return f"[LIÊN NGÂN HÀNG & OMO HÀNG NGÀY]:\n{res_interbank}\n\n[MẶT BẰNG CHUẨN BIG4]:\n{res_big4}"

def agentic_web_search(query):
    if not query.strip():
        return ""
    if TAVILY_API_KEY:
        try:
            res = requests.post("https://api.tavily.com/search", json={"api_key": TAVILY_API_KEY, "query": query, "max_results": 3}, timeout=10)
            if res.status_code == 200:
                out = [f"- [{item['title']}] {item['content']}" for item in res.json().get('results', [])]
                return "🔍 [Tavily API]\n" + "\n".join(out)
        except:
            pass
    try:
        res = DDGS().text(query, max_results=3, backend="lite")
        return "🔍 [DuckDuckGo]\n" + "\n".join([f"- [{r.get('title')}] {r.get('body')}" for r in res]) if res else ""
    except:
        return "❌ Lỗi toàn bộ Web Search"

def send_email(subject, body):
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
</html>"""

    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_USER
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
        print(f"📧 [THÀNH CÔNG] Báo cáo V33 đã được gửi đến {len(RECEIVER_EMAILS)} địa chỉ email.")
    except Exception as e:
        print(f"❌ Lỗi gửi Email: {str(e)}")

# ==========================================
# 4. BỘ NÃO TỰ ĐẢO MODEL (FALLBACK AI)
# ==========================================
def generate_ai_report_with_fallback(prompt):
    fallback_models = [
        "gemini-3.1-pro",
        "gemini-3.1-flash-lite",
        "gemini-3.0-flash",
        "gemini-3-flash",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ]

    for model_name in fallback_models:
        try:
            print(f"🤖 Kích hoạt não bộ: [{model_name}]...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"✅ THÀNH CÔNG từ [{model_name}]")
            return response.text
        except Exception as e:
            print(f"⚠️ Model [{model_name}] thất bại. Lỗi: {str(e)}")
            time.sleep(1)
            continue

    return "❌ LỖI NGHIỆM TRỌNG: Toàn bộ Model đều thất bại. Hãy kiểm tra lại API Key!"

# ==========================================
# 5. LUỒNG THỰC THI CHÍNH (MAIN AGENT LOOP)
# ==========================================
# ==========================================
# MODULE ĐỒNG THUẬN ĐA PHIÊN & THEO DÕI VỊ THẾ
# ==========================================
import json

TRACKER_FILE = "portfolio_tracker.json"

def load_portfolio_history():
    """Đọc dữ liệu 5-7 phiên gần nhất từ tracker file."""
    if not os.path.exists(TRACKER_FILE):
        return []
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("history", [])
    except Exception:
        return []

def evaluate_multi_day_positions(history, current_prices, current_vsa_dict, lookback_days=5):
    """
    Đối soát các mã đã mua trong 5 phiên qua với giá hiện tại.
    Phân loại: GIA TĂNG, CHỐT LỜI, NẮM GIỮ, hoặc CẮT LỖ.
    """
    recent_history = history[-lookback_days:] if len(history) >= lookback_days else history
    position_summary = []
    monitored_tickers = set()

    for session in reversed(recent_history):
        s_date = session.get("date", "N/A")
        picks = session.get("picks", {})

        for ticker, info in picks.items():
            if ticker in monitored_tickers:
                continue
            monitored_tickers.add(ticker)

            entry_price = info.get("entry_price", 0.0)
            target_poc = info.get("target_poc", 0.0)
            cur_price = current_prices.get(ticker, entry_price)
            vsa_info = current_vsa_dict.get(ticker, "Bình thường")

            if entry_price <= 0:
                continue

            pnl_pct = round(((cur_price - entry_price) / entry_price) * 100, 2)

            if "BÁO ĐỘNG ĐỎ" in vsa_info.upper() or pnl_pct <= -5.0:
                action = "🚨 CẮT LỖ / THOÁI VỐN NGAY"
                category = "CẮT LỖ / BẢO TOÀN VỐN"
            elif cur_price >= (target_poc * 0.98) and pnl_pct > 0:
                action = "🎯 Chốt lời 50%, nâng chặn lãi"
                category = "CHỐT LỜI TỪNG PHẦN"
            elif pnl_pct >= 2.0 and "SOS" in vsa_info.upper():
                action = "🔥 Mua gia tăng thêm 3%"
                category = "GIA TĂNG VỊ THẾ"
            else:
                action = "🛡️ Tiếp tục nắm giữ, theo dõi POC"
                category = "TIẾP TỤC NẮM GIỮ"

            position_summary.append({
                "Phân Loại": category,
                "Mã": ticker,
                "Phiên Mua": s_date,
                "Giá Vốn": entry_price,
                "Giá Hiện Tại": cur_price,
                "Lãi/Lỗ (%)": f"{pnl_pct:+0.2f}%",
                "Tín Hiệu": vsa_info,
                "Lệnh Hành Động": action
            })

    return pd.DataFrame(position_summary)

def save_today_session(history, today_str, final_picks_dict, price_dict, poc_dict):
    """Lưu lại danh mục phiên hôm nay vào file tracker."""
    new_picks = {}
    for ticker, weight in final_picks_dict.items():
        new_picks[ticker] = {
            "weight": weight,
            "entry_price": price_dict.get(ticker, 0.0),
            "target_poc": poc_dict.get(ticker, 0.0)
        }

    history.append({
        "date": today_str,
        "picks": new_picks
    })

    if len(history) > 10:
        history = history[-10:]

    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": history}, f, ensure_ascii=False, indent=2)
        
def run_quant_agent(tickers_input, macro_query):
    today_str = datetime.now().strftime('%d/%m/%Y')
    print("\n==========================================")
    print(f"🚀 KHỞI ĐỘNG AGENT QUANT TRADING (V33) LÚC {datetime.now().strftime('%H:%M:%S')}")
    print("==========================================\n")

    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    time_window, max_weight_limit = 150, 8.0  # Ép trần tối đa 8%/mã

    # Kéo Market Pulse
    df_pulse = get_ohlcv_data("E1VFVN30", days=40, max_retries=3)
    if df_pulse is None:
        error_msg = "❌ TỰ HỦY: Lỗi API lấy dữ liệu E1VFVN30. Hệ thống dừng để bảo toàn an toàn."
        print(error_msg)
        send_email("[BÁO ĐỘNG LỖI] Quant V33", error_msg)
        return

    deviation = ((df_pulse['Close'].iloc[-1] - df_pulse['Close'].tail(20).mean()) / df_pulse['Close'].tail(20).mean()) * 100
    market_status = f"GREED (+{deviation:.2f}%)" if deviation > 1.0 else f"FEAR ({deviation:.2f}%)" if deviation < -1.0 else f"NEUTRAL ({deviation:.2f}%)"

    df_bench = get_ohlcv_data("VNINDEX", days=time_window, max_retries=3)
    if df_bench is None:
        error_msg = "❌ TỰ HỦY: Lỗi API lấy dữ liệu VNINDEX. Hệ thống dừng để bảo toàn an toàn."
        print(error_msg)
        send_email("[BÁO ĐỘNG LỖI] Quant V33", error_msg)
        return
    bench_prices = df_bench['Close']

    print(f"⌛ [1/4] Cào & Phân tích Kỹ thuật cho {len(tickers)} mã...")
    data_list, raw_price_dict, micro_insights = [], {}, []
    utad_flags = {}

    for t in tickers:
        df_ohlcv = get_ohlcv_data(t, days=time_window, max_retries=3)
        if df_ohlcv is None:
            continue

        df_ohlcv['Gia_Tri_GD'] = df_ohlcv['Close'] * df_ohlcv['Volume'] * 1000
        df_ohlcv['Vol_MA20'] = df_ohlcv['Gia_Tri_GD'].rolling(window=20).mean()

        df_ohlcv['Price_Range'] = (df_ohlcv['High'] - df_ohlcv['Low']) / df_ohlcv['Close']
        df_ohlcv['is_low_vol'] = df_ohlcv['Gia_Tri_GD'] < (df_ohlcv['Vol_MA20'] * 0.6)
        df_ohlcv['is_tight_price'] = df_ohlcv['Price_Range'] < (df_ohlcv['Price_Range'].rolling(20).mean() * 0.8)

        df_ohlcv['is_down_candle'] = df_ohlcv['Close'] <= df_ohlcv['Close'].shift(1)
        df_ohlcv['is_up_candle'] = df_ohlcv['Close'] > df_ohlcv['Close'].shift(1)

        df_ohlcv['No_Supply'] = df_ohlcv['is_low_vol'] & df_ohlcv['is_tight_price'] & df_ohlcv['is_down_candle']
        df_ohlcv['No_Demand'] = df_ohlcv['is_low_vol'] & df_ohlcv['is_tight_price'] & df_ohlcv['is_up_candle']
        df_ohlcv['Can_Cung_Cluster'] = df_ohlcv['No_Supply'].rolling(window=5).sum()

        insight_text, local_poc, atr, has_utad = extract_micro_timing_insights(df_ohlcv, t)
        utad_flags[t] = has_utad
        current_price = df_ohlcv['Close'].iloc[-1]
        distance_to_poc = current_price - local_poc

        latest_status = df_ohlcv.iloc[-1]
        vsa_signal_text = "Thanh khoản bình thường."

        if latest_status['No_Demand']:
            if distance_to_poc > (atr * 2):
                vsa_signal_text = "🚨 BÁO ĐỘNG ĐỎ: Thiếu Cầu (No Demand) vùng đỉnh."
            elif distance_to_poc < 0 and abs(distance_to_poc) <= (atr * 1.5):
                vsa_signal_text = "🚨 BÁO ĐỘNG ĐỎ: Hồi phục chạm Kháng cự POC nhưng Thiếu Cầu."
        elif latest_status['No_Supply'] and latest_status['Can_Cung_Cluster'] >= 2:
            if abs(distance_to_poc) <= (atr * 1.5):
                vsa_signal_text = "🔥 VSA CHUẨN: Cạn cung (Test đáy thành công tại POC)"
            else:
                vsa_signal_text = "⚡ VSA: Thanh khoản cạn (Cần theo dõi thêm)"

        pe, roe = get_fundamentals(t)
        prices = df_ohlcv['Close']
        raw_price_dict[t] = prices
        micro_insights.append(insight_text)
        x, y, quad, mdd = calculate_rrg_and_drawdown(prices, bench_prices)

        data_list.append({
            "Mã": t,
            "Giá Hiện Tại": round(current_price, 2),
            "Vị thế RRG": quad,
            "Vùng Mua POC": round(local_poc, 2),
            "Tín hiệu VSA": vsa_signal_text,
            "P/E": pe,
            "ROE (%)": roe,
            "Max DD (%)": mdd,
            "RRG_X": x,
            "RRG_Y": y
        })
        time.sleep(0.3)

    if len(data_list) < 3:
        error_msg = "❌ TỰ HỦY: Số lượng mã đạt chuẩn thanh khoản (< 3 mã) không đủ để chạy hệ thống."
        print(error_msg)
        send_email("[CẢNH BÁO BỎ QUA] Quant V33", error_msg)
        return

    df_quant = pd.DataFrame(data_list)

    # Đếm số lượng mã trong nhóm Leading RRG
    leading_count = len(df_quant[df_quant['Vị thế RRG'] == 'Leading'])

    # Cào dữ liệu vĩ mô sớm để tính Dynamic Cash Ratio
    print("⏳ [2/4] Quét Bảng điện Vĩ mô & Đánh giá Dynamic Regime...")
    df_macro = get_macro_quant()
    search_res = agentic_web_search(macro_query)
    vn_rates_res = get_vn_interest_rates()

    regime, target_cash_ratio, target_allocation = calculate_market_regime_and_cash_ratio(df_macro, leading_count)
    print(f"📊 [CHẾ ĐỘ THỊ TRƯỜNG]: {regime} | Mục tiêu Tiền mặt: {target_cash_ratio}% | Mục tiêu Giải ngân: {target_allocation*100}%")

    # =========================================================================
    # [NÂNG CẤP V33] TRẠM KIỂM ĐỊNH HARD PRE-FILTER TRƯỚC MARKOWITZ
    # =========================================================================
    print("⏳ [3/4] Kích hoạt Trạm Kiểm Định Loại Trừ Tuyệt Đối (Hard Pre-Filter)...")
    clean_price_dict = {}
    ticker_caps = {}
    blacklisted_tickers = {}

    for index, row in df_quant.iterrows():
        t = row['Mã']
        vsa_signal = str(row['Tín hiệu VSA']).upper()
        roe = row['ROE (%)']

        # 1. Loại trừ nếu dính Báo Động Đỏ hoặc UTAD kỹ thuật
        if "BÁO ĐỘNG ĐỎ" in vsa_signal:
            blacklisted_tickers[t] = f"VSA Báo động đỏ: {row['Tín hiệu VSA']}"
            continue
        if utad_flags.get(t, False):
            blacklisted_tickers[t] = "Dính tín hiệu phân phối UTAD khung Daily"
            continue
        if pd.notna(roe) and roe < 8.0:
            blacklisted_tickers[t] = f"ROE quá thấp ({roe:.2f}%) < 8%"
            continue

        # 2. Loại trừ nếu dính OCF âm hoặc Bull-Trap Intraday từ TOOL_DeepScan_Fundamentals
        is_passed, reason = pre_screen_hard_cutoff(t)
        if not is_passed:
            blacklisted_tickers[t] = reason
            continue

        # Nếu vượt qua tất cả rào chắn thép -> Đưa vào Universe tối ưu Markowitz
        clean_price_dict[t] = raw_price_dict[t]
        ticker_caps[t] = max_weight_limit / 100.0

    print(f"🛡️ Số lượng mã vượt qua Hard Cutoff: {len(clean_price_dict)}/{len(df_quant)} mã.")

    # Chạy Tối ưu hóa Markowitz trên Clean Universe
    if len(clean_price_dict) >= 2:
        opt_weights = optimize_portfolio_monte_carlo(clean_price_dict, ticker_caps, target_allocation)
    else:
        # Fallback an toàn nếu thị trường quá xấu
        opt_weights = {t: round(target_allocation * 100 / max(1, len(clean_price_dict)), 2) for t in clean_price_dict.keys()}

    # Sắp xếp top mã giải ngân có tỷ trọng cao nhất
    sorted_weights = {k: v for k, v in sorted(opt_weights.items(), key=lambda item: item[1], reverse=True) if v > 0}
    top_5_picks = {k: sorted_weights[k] for k in list(sorted_weights.keys())[:5]}

    # Chạy DeepScan chính thức xác nhận nội tại cho Top 5
    deep_scan_report = run_deep_scan(top_5_picks)

    # Đọc lịch sử và chạy đối soát đa phiên
    history_data = load_portfolio_history()
    current_prices = {row['Mã']: row['Giá Hiện Tại'] for index, row in df_quant.iterrows()}
    current_vsa = {row['Mã']: row['Tín hiệu VSA'] for index, row in df_quant.iterrows()}
    poc_dict = {row['Mã']: row['Vùng Mua POC'] for index, row in df_quant.iterrows()}

    df_multi_day_audit = evaluate_multi_day_positions(history_data, current_prices, current_vsa, lookback_days=5)
    audit_table_markdown = df_multi_day_audit.to_string(index=False) if not df_multi_day_audit.empty else "Chưa có dữ liệu vị thế từ các phiên trước."

    # Lưu lại kết quả hôm nay vào tracker cho phiên ngày mai
    save_today_session(history_data, today_str, top_5_picks, current_prices, poc_dict)

    print("⏳ [4/4] Kích hoạt AI tổng hợp báo cáo chiến lược...")

    # Chuẩn bị chuỗi báo cáo Blacklist
    blacklist_lines = [f"* **{ticker}:** 🚨 LOẠI TRỪ TUYỆT ĐỐI do {reason}." for ticker, reason in blacklisted_tickers.items()]
    blacklist_text = "\n".join(blacklist_lines) if blacklist_lines else "* Không có mã nào dính án tử."

    # ==========================================
    # MASTER PROMPT V33 (ĐỒNG THUẬN ĐA PHIÊN & HỢP NHẤT VỊ THẾ)
    # ==========================================
    master_prompt = f"""
ĐÓNG VAI: GIÁM ĐỐC QUẢN TRỊ RỦI RO QUỸ ĐẦU TƯ (HỆ THỐNG QUANT 3D MATRIX)

[DỮ LIỆU ĐẦU VÀO LƯỢNG TỬ]
- Trạng thái Thị trường & Chế độ Vốn: {market_status} | Regime: {regime} | Mục tiêu Giải ngân: {target_allocation*100}% | Tiền mặt: {target_cash_ratio}%
- Bảng Cơ bản, RRG, Local POC & VSA Hôm nay: {df_quant.to_string()}
- Danh sách Mua Mới Hôm nay (Top Picks Markowitz Đã Ép Trần): {top_5_picks}
- Micro-Timing Wyckoff: {chr(10).join(micro_insights)}
- Vĩ mô & Hàng hóa (DXY, US10Y, VIX, Vàng, Dầu thô): {df_macro.to_string()}
- Tin tức Vĩ mô chung: {search_res}
- Dữ liệu Lãi suất Ngân hàng Việt Nam (Liên ngân hàng & Big4): {vn_rates_res}
- Hồ sơ X-Quang BCTC & Intraday của Top Picks: {deep_scan_report}
- DANH SÁCH BỊ LOẠI BỞI HARD PRE-FILTER HÔM NAY:
{blacklist_text}

[BẢNG ĐỐI SOÁT VỊ THẾ 5 PHIÊN GẦN NHẤT ĐÃ TÍNH TOÁN]:
{audit_table_markdown}

[QUY TẮC ĐIỀU HÀNH ĐỒNG THUẬN ĐA PHIÊN & VĨ MÔ NGHỊCH LÝ]
1. Vĩ mô: Nếu DXY hoặc US10Y hạ nhiệt/tạo đỉnh ngắn hạn + VIX < 25 + Ngành Leading xuất hiện: Chế độ SELECTIVE EXPANSION, nới lỏng giải ngân lên {target_allocation*100}%. Nếu US10Y > 5.2% hoặc DXY tăng nóng: Chế độ DEFENSIVE, giữ tiền mặt cao ({target_cash_ratio}%).
2. Tích hợp vị thế đa phiên: Kết hợp các mã đã khuyến nghị ở 5 phiên trước cùng các mã Mua Mới hôm nay ({top_5_picks}) thành 1 Bảng Điều Hành Vị Thế duy nhất.
3. Mã vi phạm OCF âm (như HCM, DCM) hoặc dính UTAD/Bull-trap hôm nay ĐÃ BỊ GẠCH TÊN HOÀN TOÀN và nằm trọn vẹn ở Mục 3.
4. Quy tắc Định giá Cổ phiếu theo Lãi suất & Hàng hóa (Chống nhiễu báo chí):
   - RÀO CHẮN CHỐNG NHIỄU: Chỉ sử dụng Lãi suất Liên ngân hàng qua đêm (NHNN) và Lãi suất nhóm Big4 (VCB, BID, CTG, Agribank) làm chuẩn. BỎ QUA tin giật tít của ngân hàng nhỏ hoặc lãi suất đặc biệt hàng trăm tỷ.
   - Khi Lãi suất Liên ngân hàng < 4.0% và huy động 12M Big4 <= 5.5%: Thanh khoản dồi dào, đánh giá TÍCH CỰC cho nhóm Ngân hàng (VCB, BID, CTG, TCB, MBB) và BĐS Khu công nghiệp (IDC, VGC, PHR).
   - Khi Lãi suất Liên ngân hàng vọt > 5.0% hoặc Big4 rục rịch tăng: Cảnh báo chi phí nợ cho nhóm BĐS dân dụng, Xây dựng, Thép; ưu tiên tuyệt đối doanh nghiệp giàu tiền mặt gửi ngân hàng (DGC, FPT, VNM, SAB, NTC).
   - Giá Dầu thô: Tăng mạnh hỗ trợ nhóm Dầu khí (PVD, PVS, GAS), nhưng tăng quá nóng sẽ cảnh báo rủi ro lạm phát đầu vào.
   - Giá Vàng: Đo lường tâm lý trú ẩn địa chính trị và áp lực tỷ giá USD/VND.

NHIỆM VỤ: Bạn BẮT BUỘC sinh ra báo cáo theo ĐÚNG 100% Cấu trúc Markdown dưới đây:

# BÁO CÁO QUẢN TRỊ RỦI RO & ĐỊNH HƯỚNG ĐẦU TƯ NGÀY {today_str}
**Người trình bày:** Giám đốc Quản trị Rủi ro Quỹ Đầu tư

## 1. TỔNG QUAN VĨ MÔ & THỊ TRƯỜNG
Đánh giá Vĩ mô theo "Luật Đánh Giá Vĩ Mô Nghịch Lý & Quy Tắc Thích Ứng Mới":

- **Tin tức & Lãi suất Nội địa:** [Tóm tắt tin vĩ mô và mặt bằng Lãi suất Tiết kiệm / Cho vay của các ngân hàng Việt Nam hôm nay].
- **Yếu tố Toán học & Hàng hóa Chiến lược:**
  - DXY (Chỉ số USD): [Mức hiện tại và biến động %]
  - US10Y (Lợi suất TP Mỹ): [Mức hiện tại và biến động %]
  - VIX (Chỉ số Sợ hãi): [Mức hiện tại và biến động %]
  - Gold (Vàng thế giới): [Mức hiện tại USD/oz và biến động %]
  - Crude Oil (Dầu thô WTI): [Mức hiện tại USD/thùng và biến động %]
  - Lãi suất Liên ngân hàng & Big4: [Tóm tắt xu hướng và mức lãi suất phổ biến từ dữ liệu quét được]
- **Tác động Lãi suất & Hàng hóa lên Cổ phiếu:** [Phân tích 1-2 câu về xu hướng lãi suất tiết kiệm/cho vay và giá Vàng/Dầu đang tác động tích cực hay tiêu cực đến các nhóm ngành trong danh mục].
- **Dựa trên luật:** [Áp dụng dữ liệu vào luật vĩ mô và phân tích trạng thái thích ứng {regime}].
- **Chốt:** Rủi ro [THẤP / TRUNG BÌNH / CAO]. Định hướng: [1 câu tóm tắt chiến lược phân bổ vốn].

## 2. BẢNG ĐIỀU HÀNH VỊ THẾ HỢP NHẤT (HÀNH ĐỘNG HÔM NAY)
Tổng hợp vị thế chu kỳ 5 phiên gần nhất cùng các lệnh giải ngân mới phiên hôm nay:

[TẠO BẢNG MARKDOWN HỢP NHẤT:
Các cột BẮT BUỘC: Phân Loại | Mã | Phiên Mua | Giá Vốn | Giá Hiện Tại | Lãi/Lỗ (%) | Tín Hiệu Đa Phiên | Lệnh Hành Động Hôm Nay]

*(Lưu ý: Nếu bảng đối soát 5 phiên trước chưa có dữ liệu, hãy hiển thị danh sách 5 mã Mua Mới của hôm nay kèm tỷ trọng giải ngân).*

- **Tổng tỷ trọng cổ phiếu danh mục sau điều phối:** [TỔNG TỶ TRỌNG CỔ PHIẾU ĐANG NẮM GIỮ VÀ MUA MỚI]%.
- **Đánh giá hiệu quả các phiên trước:** [Nhận xét 1-2 câu ngắn gọn về diễn biến lời/lỗ của các mã đã khuyến nghị trước đó].

## 3. CẢNH BÁO RỦI RO ĐỎ (DANH SÁCH LOẠI TRỪ TUYỆT ĐỐI)
Chúng tôi lưu ý các mã sau đây ĐÃ BỊ LOẠI BỎ NGAY TỪ VÒNG SƠ LOẠI ĐẦU VÀO, không đưa vào danh mục giải ngân:

{blacklist_text}

**Khuyến nghị:** HỦY LỆNH đối với các mã trong danh sách cảnh báo, tuyệt đối không giải ngân.

## 4. LỆNH ĐIỀU ĐỘNG TỪ GIÁM ĐỐC QUỸ
- Trạng thái Vĩ mô [{regime}] và thị trường là cơ hội để [giải ngân có chọn lọc / phòng thủ].
- Tuân thủ chặt chẽ các điểm Stoploss dựa trên POC hoặc ATR để quản lý rủi ro.

**Tính toán Tỷ lệ Tiền mặt:**
- Tổng tỷ trọng cổ phiếu toàn danh mục: [ĐIỀN TỔNG TỶ TRỌNG CỔ PHIẾU]%
- Tỷ lệ Tiền mặt = 100% - [ĐIỀN TỔNG TỶ TRỌNG]% = [TÍNH: 100 TRỪ TỔNG TỶ TRỌNG]%

**Hướng dẫn đặt lệnh:**
- Đối với mã MUA MỚI: Giải ngân tại Giá Hiện Tại theo tỷ trọng đã định mức.
- Đối với mã GIA TĂNG: Mua thêm theo đúng tỷ trọng điều động.
- Đối với mã NẮM GIỮ / CHỐT LỜI: Đặt Target Chốt Lời tại POC, nâng ngưỡng chặn lãi Trailing Stop.
- Đối với mã CẮT LỖ: Thoái vốn ngay tại giá thị trường để bảo toàn vốn.
"""

    final_report = generate_ai_report_with_fallback(master_prompt)
    print("\n==========================================")
    print("📑 BÁO CÁO NỘI TẠI (AGENT SKILL V33)")
    print("==========================================\n")
    print(final_report)
    print("\n==========================================")

    # GỬI EMAIL CHỐT HẠ
    email_subject = f"[Quant 3D Matrix] Lệnh Điều Động Vốn Ngày {today_str}"
    send_email(email_subject, final_report)

    return final_report


if __name__ == "__main__":
    FULL_WATCHLIST = "VCB, BID, CTG, TCB, MBB, SSI, VND, VHM, VIC, VRE, HPG, HSG, PVD, PVS, DGC, DCM, DPM, VHC, ANV, PTB, MWG, PNJ, FPT, REE, GAS, NT2, VSH, VNM, SAB, KBC, SZC, IDC, VGC, DIG, NVL, PDR, DXG, KDH, NKG, VGS, SMC, VCI, HCM, SIP, DTD, NTC, PHR, GVR"
    MACRO_KEYWORDS = "Tổng hợp tin tức Vĩ mô Việt Nam (Lãi suất, Tỷ giá, Đầu tư công) VÀ Điểm nóng kinh tế, rủi ro địa chính trị thế giới mới nhất hôm nay"

    run_quant_agent(FULL_WATCHLIST, MACRO_KEYWORDS)
