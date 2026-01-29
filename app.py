import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import warnings

warnings.filterwarnings("ignore")

# ==========================================
# 1. ตั้งค่าและฟังก์ชัน Telegram
# ==========================================
st.set_page_config(page_title="Super Sniper V.5", layout="wide", page_icon="✈️")

def send_telegram_message(message):
    """ฟังก์ชันส่งข้อความเข้า Telegram"""
    # เช็คว่ามีกุญแจครบไหม
    if 'telegram_token' in st.secrets and 'telegram_chat_id' in st.secrets:
        token = st.secrets['telegram_token']
        chat_id = st.secrets['telegram_chat_id']
        
        # ยิง API ไปหา Telegram
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                st.error(f"⚠️ ส่งไม่ผ่าน: {response.text}")
        except Exception as e:
            st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")
            
    else:
        st.warning("⚠️ ขาด telegram_token หรือ telegram_chat_id ใน Secrets")

# ==========================================
# 2. ข้อมูลหุ้นและกองทุน
# ==========================================
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK" , "PTTEP.BK"
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
# 3. ส่วนแสดงผล (User Interface)
# ==========================================
st.sidebar.title("✈️ Sniper Bot")
mode = st.sidebar.radio("เลือกโหมด:", ["🇹🇭 หุ้นรายตัว", "🌎 กองทุนรวม"])
st.sidebar.markdown("---")

# ปุ่มกดเรียกบอท (Telegram Trigger)
if st.sidebar.button("🚀 สแกน & ส่งเข้า Telegram"):
    with st.spinner("กำลังส่งข้อมูลให้บอท BoSniper..."):
        
        # 1. สแกนหุ้นไทย (เกณฑ์ 30)
        msg_stocks = ""
        for sym in THAI_STOCKS:
            df = get_data(sym)
            if df is not None:
                df['RSI'] = calculate_rsi(df['Close'])
                rsi = df['RSI'].iloc[-1]
                if rsi <= 30: 
                    msg_stocks += f"\n🎯 *{sym.replace('.BK','')}* (RSI {rsi:.1f}) ✅"
        
        # 2. สแกนกองทุน (เกณฑ์ 45)
        msg_funds = ""
        for name, info in FUND_MAPPING.items():
            df = get_data(info['ticker'])
            if df is not None:
                df['RSI'] = calculate_rsi(df['Close'])
                rsi = df['RSI'].iloc[-1]
                if rsi <= 45:
                    msg_funds += f"\n🛒 *{name}* (RSI {rsi:.1f})"

        # 3. ส่งข้อความ
        full_msg = ""
        if msg_stocks: full_msg += f"\n\n🇹🇭 *หุ้นไทยของถูก:*{msg_stocks}"
        if msg_funds: full_msg += f"\n\n🌎 *กองทุนน่าสะสม:*{msg_funds}"
        
        if full_msg != "":
            send_telegram_message(f"🔥 *Sniper Report* 🔥{full_msg}")
            st.success("✅ ส่งเข้า Telegram เรียบร้อย!")
        else:
            send_telegram_message("☕ *Sniper Report:* ตลาดเงียบครับ ไม่มีสัญญาณซื้อ (Wait)")
            st.info("ส่งรายงานสถานะเข้า Telegram แล้ว")

# --- ส่วนแสดงผลตาราง ---
if mode == "🇹🇭 หุ้นรายตัว":
    st.title("🇹🇭 Sniper Stock")
    results = []
    for symbol in THAI_STOCKS:
        df = get_data(symbol)
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            price = df['Close'].iloc[-1]
            signal, color = "WAIT ✋", "gray"
            if rsi <= 30: signal, color = "FIRE! (BUY) 🔫", "green"
            elif rsi >= 70: signal, color = "TAKE PROFIT 💰", "red"
            results.append({"Symbol": symbol, "Price": price, "RSI": rsi, "Signal": signal, "Color": color})
            
    for res in results:
        with st.container(border=True):
            cols = st.columns([2,1,2])
            cols[0].markdown(f"**{res['Symbol'].replace('.BK','')}**")
            cols[1].markdown(f"RSI: **{res['RSI']:.1f}**")
            if res['Color']=='green': cols[2].success(res['Signal'])
            elif res['Color']=='red': cols[2].error(res['Signal'])
            else: cols[2].info(res['Signal'])

else: # กองทุน
    st.title("🌎 Sniper Fund")
    results = []
    for name, info in FUND_MAPPING.items():
        df = get_data(info['ticker'])
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            signal, color = "WAIT ✋", "gray"
            if rsi <= 30: signal, color = "MUST BUY! 💎", "green"
            elif rsi <= 45: signal, color = "ACCUMULATE 🛒", "light_green"
            elif rsi >= 75: signal, color = "OVERHEATED 🔥", "red"
            results.append({"Name": name, "RSI": rsi, "Signal": signal, "Color": color})

    for res in results:
        with st.container(border=True):
            cols = st.columns([3,1,2])
            cols[0].markdown(f"**{res['Name']}**")
            cols[1].markdown(f"RSI: **{res['RSI']:.1f}**")
            if 'green' in res['Color']: cols[2].success(res['Signal'])
            elif 'red' in res['Color']: cols[2].error(res['Signal'])
            else: cols[2].info(res['Signal'])