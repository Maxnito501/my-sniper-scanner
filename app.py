import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import warnings

warnings.filterwarnings("ignore")

# ==========================================
# 1. ตั้งค่าและฟังก์ชัน Telegram
# ==========================================
st.set_page_config(page_title="Super Sniper V.6", layout="wide", page_icon="✈️")

def send_telegram_message(message):
    """ฟังก์ชันส่งข้อความเข้า Telegram"""
    if 'telegram_token' in st.secrets and 'telegram_chat_id' in st.secrets:
        token = st.secrets['telegram_token']
        chat_id = st.secrets['telegram_chat_id']
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
    else:
        st.warning("⚠️ ขาด Token ใน Secrets")

# ==========================================
# 2. ข้อมูลหุ้นและกองทุน
# ==========================================
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"
]

FUND_MAPPING = {
    "SCBSEMI (Semiconductor)":   {"ticker": "SMH", "market": "US"},
    "SCBRMNDQ (NASDAQ 100)":     {"ticker": "QQQ", "market": "US"},
    "SCBRMS&P500 (S&P 500)":     {"ticker": "SPY", "market": "US"},
    "SCBGQUAL (Global Quality)": {"ticker": "QUAL", "market": "US"},
    "KKP GB THAI ESG (Thai ESG)":{"ticker": "^SET", "market": "TH"},
    "TISCO (High Dividend)":     {"ticker": "TISCO.BK", "market": "TH"},
    "Gold (ทองคำโลก)":           {"ticker": "GLD", "market": "US"}
}

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if len(df) == 0: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return None

# ==========================================
# 3. ส่วนแสดงผล (Sidebar & Button)
# ==========================================
st.sidebar.title("✈️ Sniper Bot V.6")
mode = st.sidebar.radio("เลือกโหมด:", ["🇹🇭 หุ้นรายตัว", "🌎 กองทุนรวม"])
st.sidebar.markdown("---")

# ปุ่มกดเรียกบอท
if st.sidebar.button("🚀 สแกน & ส่งเข้า Telegram"):
    with st.spinner("กำลังส่งข้อมูลให้บอท BoSniper..."):
        msg_stocks = ""
        for sym in THAI_STOCKS:
            df = get_data(sym)
            if df is not None:
                df['RSI'] = calculate_rsi(df['Close'])
                rsi = df['RSI'].iloc[-1]
                if rsi <= 30: msg_stocks += f"\n🎯 *{sym.replace('.BK','')}* (RSI {rsi:.1f}) ✅"
        
        msg_funds = ""
        for name, info in FUND_MAPPING.items():
            df = get_data(info['ticker'])
            if df is not None:
                df['RSI'] = calculate_rsi(df['Close'])
                rsi = df['RSI'].iloc[-1]
                if rsi <= 45: msg_funds += f"\n🛒 *{name}* (RSI {rsi:.1f})"

        full_msg = ""
        if msg_stocks: full_msg += f"\n\n🇹🇭 *หุ้นไทย:*{msg_stocks}"
        if msg_funds: full_msg += f"\n\n🌎 *กองทุน:*{msg_funds}"
        
        if full_msg != "":
            send_telegram_message(f"🔥 *Sniper Report* 🔥{full_msg}")
            st.success("✅ ส่งเข้า Telegram เรียบร้อย!")
        else:
            send_telegram_message("☕ *Sniper Report:* ตลาดเงียบครับ (Wait)")
            st.info("ส่งสถานะเข้า Telegram แล้ว")

# ==========================================
# 4. ส่วนแสดงผลกราฟและตาราง (Main Area)
# ==========================================
if mode == "🇹🇭 หุ้นรายตัว":
    st.title("🇹🇭 Sniper Stock (พร้อมกราฟ)")
    for symbol in THAI_STOCKS:
        df = get_data(symbol)
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            price = df['Close'].iloc[-1]
            signal, color = "WAIT ✋", "gray"
            if rsi <= 30: signal, color = "FIRE! (BUY) 🔫", "green"
            elif rsi >= 70: signal, color = "TAKE PROFIT 💰", "red"
            
            # การแสดงผล
            with st.container(border=True):
                c1, c2, c3 = st.columns([2,1,2])
                c1.markdown(f"### {symbol.replace('.BK','')}")
                c2.markdown(f"Price: **{price:.2f}**")
                c3.markdown(f"RSI: **{rsi:.1f}**")
                
                if color=='green': st.success(signal)
                elif color=='red': st.error(signal)
                else: st.info(signal)
                
                # --- ส่วนกราฟ (เอากลับมาแล้ว!) ---
                st.line_chart(df['Close'], color="#00FF00" if color=="green" else "#FF0000" if color=="red" else "#808080")

else: # กองทุน
    st.title("🌎 Sniper Fund (พร้อมกราฟ)")
    for name, info in FUND_MAPPING.items():
        df = get_data(info['ticker'])
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            signal, color = "WAIT ✋", "gray"
            if rsi <= 30: signal, color = "MUST BUY! 💎", "green"
            elif rsi <= 45: signal, color = "ACCUMULATE 🛒", "light_green"
            elif rsi >= 75: signal, color = "OVERHEATED 🔥", "red"
            
            with st.container(border=True):
                st.markdown(f"### {name}")
                st.markdown(f"RSI: **{rsi:.1f}**")
                
                if 'green' in color: st.success(signal)
                elif 'red' in color: st.error(signal)
                else: st.info(signal)

                # --- ส่วนกราฟ (เอากลับมาแล้ว!) ---
                st.line_chart(df['Close'])