import streamlit as st
import yfinance as yf
import pandas as pd
import warnings

# ปิด Warning ที่น่ารำคาญ
warnings.filterwarnings("ignore")

# ==========================================
# 1. ตั้งค่าหน้าเว็บ (สังเกตคำว่า V.2)
# ==========================================
st.set_page_config(page_title="Super Sniper V.2", layout="wide", page_icon="🎯")

# ==========================================
# 2. ข้อมูลหุ้นและกองทุน (DATA CONFIG)
# ==========================================

# รายชื่อหุ้นรายตัว (Stocks)
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"
]

# รายชื่อกองทุน (Mapping กองไทย -> กองแม่/ดัชนีโลก)
FUND_MAPPING = {
    "SCBSEMI (Semiconductor)":   {"ticker": "SMH", "market": "US", "desc": "VanEck Semiconductor ETF"},
    "SCBRMNDQ (NASDAQ 100)":     {"ticker": "QQQ", "market": "US", "desc": "Invesco QQQ Trust"},
    "SCBRMS&P500 (S&P 500)":     {"ticker": "SPY", "market": "US", "desc": "SPDR S&P 500 ETF"},
    "SCBGQUAL (Global Quality)": {"ticker": "QUAL", "market": "US", "desc": "iShares MSCI USA Quality"},
    "KKP GB THAI ESG (Thai ESG)":{"ticker": "^SET", "market": "TH", "desc": "SET Index (ตัวแทนตลาดไทย)"},
    "TISCO (High Dividend)":     {"ticker": "TISCO.BK", "market": "TH", "desc": "หุ้น TISCO (ปันผลสูง)"},
    "Gold (ทองคำโลก)":           {"ticker": "GLD", "market": "US", "desc": "SPDR Gold Shares"}
}

# ==========================================
# 3. ฟังก์ชันคำนวณ (CORE LOGIC)
# ==========================================
def calculate_rsi(series, period=14):
    """คำนวณ RSI แบบไม่ง้อ Library pandas_ta"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_data(ticker, period="6mo"):
    """ดึงข้อมูลราคาหุ้น"""
    try:
        # auto_adjust=True เพื่อให้ราคาถูกต้องที่สุด
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if len(df) == 0: return None
        
        # แก้ปัญหา Column ซ้อน (MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except: return None

# ==========================================
# 4. ส่วนแสดงผล (User Interface)
# ==========================================

# --- Sidebar เมนูด้านซ้าย ---
st.sidebar.title("🎯 Super Sniper Control")
st.sidebar.info("เวอร์ชัน V.2 (อัปเดตล่าสุด)") # เช็คตรงนี้ได้เลย
mode = st.sidebar.radio("เลือกโหมดเล็งเป้า:", ["🇹🇭 หุ้นรายตัว (Stocks)", "🌎 กองทุนรวม (Funds)"])
st.sidebar.markdown("---")
rsi_period = st.sidebar.slider("ความไว RSI", 7, 30, 14)

# ------------------------------------------
# MODE 1: หุ้นรายตัว (Stocks)
# ------------------------------------------
if mode == "🇹🇭 หุ้นรายตัว (Stocks)":
    st.title("🇹🇭 Sniper Stock V.2: หุ้นรายตัว")
    
    selected_stocks = st.sidebar.multiselect("เลือกหุ้น:", THAI_STOCKS, default=THAI_STOCKS)
    rsi_lower = st.sidebar.number_input("จุดเข้าซื้อ (RSI Buy)", value=30)
    rsi_upper = st.sidebar.number_input("จุดขายทำกำไร (RSI Sell)", value=70)

    results = []
    for symbol in selected_stocks:
        df = get_data(symbol)
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'], period=rsi_period)
            try:
                # ดึงค่าล่าสุด (ใช้ .item() เพื่อความชัวร์)
                last_price = float(df['Close'].iloc[-1].item()) if hasattr(df['Close'].iloc[-1], 'item') else float(df['Close'].iloc[-1])
                last_rsi = float(df['RSI'].iloc[-1].item()) if hasattr(df['RSI'].iloc[-1], 'item') else float(df['RSI'].iloc[-1])
                prev_price = float(df['Close'].iloc[-2].item()) if hasattr(df['Close'].iloc[-2], 'item') else float(df['Close'].iloc[-2])
            except: continue

            change = ((last_price - prev_price)/prev_price)*100
            
            # Logic สัญญาณไฟ
            signal = "WAIT ✋"
            color = "gray"
            if last_rsi <= rsi_lower:
                signal = "FIRE! (BUY) 🔫"
                color = "green"
            elif last_rsi >= rsi_upper:
                signal = "TAKE PROFIT 💰"
                color = "red"
            elif last_rsi <= rsi_lower + 5:
                signal = "PREPARE ⚠️"
                color = "orange"
            
            results.append({"Symbol": symbol, "Price": last_price, "Change": change, "RSI": last_rsi, "Signal": signal, "Color": color})

    # แสดงผล
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        st.subheader("📡 Radar Scan")
        for res in results:
            with st.container(border=True):
                st.markdown(f"#### {res['Symbol'].replace('.BK','')}")
                st.markdown(f"ราคา: {res['Price']:.2f} ({res['Change']:+.2f}%)")
                st.markdown(f"RSI: **{res['RSI']:.1f}**")
                if res['Color']=='green': st.success(res['Signal'])
                elif res['Color']=='red': st.error(res['Signal'])
                elif res['Color']=='orange': st.warning(res['Signal'])
                else: st.info(res['Signal'])
    
    with c2:
        st.subheader("📈 Chart (6 เดือน)")
        chart_sym = st.selectbox("เลือกดูกราฟหุ้น:", selected_stocks)
        df_chart = get_data(chart_sym)
        if df_chart is not None:
            st.line_chart(df_chart['Close'])

# ------------------------------------------
# MODE 2: กองทุนรวม (Funds)
# ------------------------------------------
else:
    st.title("🌎 Sniper Fund V.2: กองทุนโลก")
    st.info("💡 กราฟอ้างอิงจาก **ETF กองแม่** (Real-time ตลาดโลก) เพื่อใช้ดักทางกองทุนไทย")
    
    selected_funds = st.sidebar.multiselect("เลือกกองทุน:", list(FUND_MAPPING.keys()), default=list(FUND_MAPPING.keys()))
    
    results = []
    for name in selected_funds:
        info = FUND_MAPPING[name]
        df = get_data(info['ticker'])
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'], period=rsi_period)
            try:
                last_rsi = float(df['RSI'].iloc[-1].item()) if hasattr(df['RSI'].iloc[-1], 'item') else float(df['RSI'].iloc[-1])
                last_price = float(df['Close'].iloc[-1].item()) if hasattr(df['Close'].iloc[-1], 'item') else float(df['Close'].iloc[-1])
            except: continue
            
            # Logic กองทุน (เน้นสะสม)
            signal = "WAIT (ถือ/รอ) ✋"
            color = "gray"
            if last_rsi <= 30:
                signal = "MUST BUY! (ของถูกมาก) 💎"
                color = "green"
            elif last_rsi <= 40:
                signal = "ACCUMULATE (เริ่มสะสม) 🛒"
                color = "light_green"
            elif last_rsi >= 75:
                signal = "OVERHEATED (ร้อนแรงเกิน) 🔥"
                color = "red"
            
            results.append({"Name": name, "Master": info['ticker'], "RSI": last_rsi, "Price": last_price, "Signal": signal, "Color": color})

    # แสดงผล
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        st.subheader("📡 Fund Status")
        for res in results:
            with st.container(border=True):
                st.markdown(f"#### {res['Name']}")
                st.caption(f"Tracking: {res['Master']}")
                st.markdown(f"RSI: **{res['RSI']:.1f}**")
                
                if res['Color']=='green': st.success(res['Signal'])
                elif res['Color']=='light_green': st.success(res['Signal'])
                elif res['Color']=='red': st.error(res['Signal'])
                else: st.info(res['Signal'])

    with c2:
        st.subheader("📈 Master Fund Chart")
        chart_fund = st.selectbox("เลือกดูกราฟกองทุน:", selected_funds)
        info = FUND_MAPPING[chart_fund]
        df_chart = get_data(info['ticker'])
        if df_chart is not None:
            st.line_chart(df_chart['Close'])
            if info['market'] == "US":
                st.warning("⚠️ ตลาด US เปิด 20:30 น. (ช่วงเช้ากราฟอาจจะไม่ขยับ)")