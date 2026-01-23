import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import warnings

# ปิดการแจ้งเตือนจุกจิก
warnings.filterwarnings("ignore")

# ==========================================
# 1. ตั้งค่าหน้าเว็บและฟังก์ชัน Telegram
# ==========================================
st.set_page_config(page_title="BoSniper V.6", layout="wide", page_icon="✈️")

def send_telegram_message(message):
    """ฟังก์ชันส่งข้อความเข้ามือถือผ่าน Telegram"""
    # เช็คว่ามี Token ใน Secrets หรือยัง
    if 'telegram_token' in st.secrets and 'telegram_chat_id' in st.secrets:
        token = st.secrets['telegram_token']
        chat_id = st.secrets['telegram_chat_id']
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            st.error(f"⚠️ Error ส่งข้อความไม่ได้: {e}")
    else:
        st.warning("⚠️ ยังไม่ได้ใส่ Token ใน Secrets")

# ==========================================
# 2. รายชื่อหุ้นและกองทุนที่ต้องการเฝ้า
# ==========================================
# หุ้นไทย (เติมเพิ่มได้ตามใจชอบ)
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"
]

# กองทุนรวมและสินทรัพย์โลก (Mapping ชื่อกองทุน -> สัญลักษณ์ตลาดโลก)
FUND_MAPPING = {
    "SCBSEMI (Semiconductor)":   {"ticker": "SMH", "market": "US"},
    "SCBRMNDQ (NASDAQ 100)":     {"ticker": "QQQ", "market": "US"},
    "SCBRMS&P500 (S&P 500)":     {"ticker": "SPY", "market": "US"},
    "SCBGQUAL (Global Quality)": {"ticker": "QUAL", "market": "US"},
    "KKP GB THAI ESG (Thai ESG)":{"ticker": "^SET", "market": "TH"},
    "TISCO (High Dividend)":     {"ticker": "TISCO.BK", "market": "TH"},
    "Gold (ทองคำโลก)":           {"ticker": "GLD", "market": "US"}
}

# ==========================================
# 3. ฟังก์ชันคำนวณ RSI และดึงข้อมูล
# ==========================================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=300) # ช่วยจำข้อมูล 5 นาที แอปจะได้ไม่หน่วง
def get_data(ticker):
    try:
        # ดึงย้อนหลัง 6 เดือน เพื่อให้กราฟสวยและคำนวณ RSI แม่น
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if len(df) == 0: return None
        # แก้ปัญหา MultiIndex ของ yfinance เวอร์ชันใหม่
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return None

# ==========================================
# 4. ส่วน Sidebar (เมนูซ้ายมือ)
# ==========================================
st.sidebar.title("✈️ BoSniper Command")
st.sidebar.markdown("ระบบเฝ้าตลาดอัจฉริยะ")
mode = st.sidebar.radio("เลือกโหมดแสดงผล:", ["🇹🇭 หุ้นรายตัว", "🌎 กองทุนรวม"])
st.sidebar.markdown("---")

# ปุ่มกดสแกนและส่งเข้ามือถือ
if st.sidebar.button("🚀 สแกน & ส่งเข้า Telegram"):
    status_box = st.sidebar.empty()
    status_box.info("⏳ กำลังสแกนตลาด...")
    
    msg_stocks = ""
    # 1. สแกนหุ้นไทย (RSI <= 30)
    for sym in THAI_STOCKS:
        df = get_data(sym)
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            if rsi <= 30: 
                msg_stocks += f"\n🎯 *{sym.replace('.BK','')}* (RSI {rsi:.1f}) ✅"
    
    msg_funds = ""
    # 2. สแกนกองทุน (RSI <= 45)
    for name, info in FUND_MAPPING.items():
        df = get_data(info['ticker'])
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            if rsi <= 45: 
                msg_funds += f"\n🛒 *{name}* (RSI {rsi:.1f})"

    # 3. รวมข้อความส่ง
    full_msg = ""
    if msg_stocks: full_msg += f"\n\n🇹🇭 *หุ้นไทย (Buy):*{msg_stocks}"
    if msg_funds: full_msg += f"\n\n🌎 *กองทุน (Accumulate):*{msg_funds}"
    
    if full_msg != "":
        send_telegram_message(f"🔥 *Sniper Report* 🔥{full_msg}")
        status_box.success("✅ ส่งเข้ามือถือแล้ว!")
    else:
        send_telegram_message("☕ *Sniper Report:* ตลาดเงียบครับ (Wait)")
        status_box.info("ตลาดเงียบ ส่งสถานะ Wait แล้ว")

# ==========================================
# 5. ส่วนแสดงผลหลัก (Main Dashboard)
# ==========================================
if mode == "🇹🇭 หุ้นรายตัว":
    st.title("🇹🇭 Sniper Stock (หุ้นไทย)")
    st.markdown("เกณฑ์: **RSI <= 30** คือจุดเข้าซื้อ")
    
    for symbol in THAI_STOCKS:
        df = get_data(symbol)
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            price = df['Close'].iloc[-1]
            
            # กำหนดสีและคำแนะนำ
            signal, color = "WAIT ✋", "gray"
            if rsi <= 30: signal, color = "FIRE! (BUY) 🔫", "green"
            elif rsi >= 70: signal, color = "TAKE PROFIT 💰", "red"
            
            # การแสดงผล Card
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                c1.markdown(f"### {symbol.replace('.BK','')}")
                c2.markdown(f"RSI: **{rsi:.1f}**")
                c3.markdown(f"Price: **{price:.2f}**")
                
                if color=='green': st.success(signal)
                elif color=='red': st.error(signal)
                else: st.info(signal)
                
                # กราฟราคา
                st.line_chart(df['Close'], color="#00FF00" if color=="green" else "#FF0000" if color=="red" else "#808080")

else: # โหมดกองทุน
    st.title("🌎 Sniper Fund (กองทุนรวม)")
    st.markdown("เกณฑ์: **RSI <= 45** (ทยอยสะสม), **RSI <= 30** (จัดหนัก)")
    
    for name, info in FUND_MAPPING.items():
        df = get_data(info['ticker'])
        if df is not None:
            df['RSI'] = calculate_rsi(df['Close'])
            rsi = df['RSI'].iloc[-1]
            price = df['Close'].iloc[-1]
            
            signal, color = "WAIT ✋", "gray"
            if rsi <= 30: signal, color = "MUST BUY! 💎", "green"
            elif rsi <= 45: signal, color = "ACCUMULATE 🛒", "light_green" # สีเขียวอ่อน
            elif rsi >= 75: signal, color = "OVERHEATED 🔥", "red"
            
            with st.container(border=True):
                st.markdown(f"### {name}")
                c1, c2 = st.columns(2)
                c1.markdown(f"RSI: **{rsi:.1f}**")
                c2.markdown(f"Asset Price: **{price:.2f}**")
                
                if 'green' in color: st.success(signal)
                elif 'red' in color: st.error(signal)
                else: st.info(signal)

                st.line_chart(df['Close'])