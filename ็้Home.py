import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import google.generativeai as genai

# --- 1. Global Configuration & Theme ---
st.set_page_config(
    page_title="POLARIS: Unified Command Center",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS for Premium Engineering Look
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .stMetric { background-color: white !important; border-radius: 12px !important; border: 1px solid #e2e8f0 !important; padding: 15px !important; }
    .strategy-note { background-color: #f1f5f9; padding: 15px; border-radius: 12px; border-left: 5px solid #334155; margin-bottom: 10px; }
    .zing-tag { background: #fee2e2; color: #ef4444; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    .buy-tag { background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Shared Utilities (API & Data) ---
def get_analysis_data(ticker):
    """ฟังก์ชันกลางสำหรับดึงข้อมูลและคำนวณ RSI, Volume Ratio"""
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if data.empty: return None
        close = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
        vol = data['Volume'].iloc[:, 0] if isinstance(data['Volume'], pd.DataFrame) else data['Volume']
        
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Vol Ratio (5-day avg)
        avg_vol = vol.iloc[-6:-1].mean()
        vol_ratio = vol.iloc[-1] / avg_vol if avg_vol > 0 else 0
        
        curr_p = float(close.iloc[-1])
        change = ((curr_p - close.iloc[-2]) / close.iloc[-2]) * 100
        
        return {
            "price": round(curr_p, 2),
            "rsi": round(float(rsi.iloc[-1]), 2),
            "vol_ratio": round(float(vol_ratio), 2),
            "change": round(float(change), 2)
        }
    except: return None

def ai_news_impact(news, symbols):
    """ระบบ AI วิเคราะห์ข่าว (ชุดที่ 2)"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        prompt = f"Analyze this news: '{news}' for stocks: {symbols}. Predict impact (+/- Score), sentiment, and suggest action: Buy/Hold/Wait."
        response = model.generate_content(prompt)
        return response.text
    except: return "AI analysis unavailable."

# --- 3. Battle Sets (The Modules) ---

def set_1_wealth_intelligence():
    """ชุดที่ 1: หุ้นแกร่ง & ภาษี (1, 3, 6, 8)"""
    st.header("⚖️ ชุดที่ 1: Wealth Hub (หุ้นแกร่ง & ภาษี)")
    t1, t2, t3 = st.tabs(["📈 สแกน RSI & eDCA (1, 6)", "💰 เช็กความคุ้ม & ปันผล (8)", "📅 แผนวันที่ซื้อ DCA (3)"])
    
    with t1:
        st.subheader("หาจังหวะสะสมหุ้นแกร่ง & กองทุน RMF")
        funds = {"Nasdaq": "^NDX", "S&P500": "^GSPC", "SET50": "^SET50.BK", "Quality": "QUAL"}
        cols = st.columns(len(funds))
        for i, (name, tick) in enumerate(funds.items()):
            d = get_analysis_data(tick)
            if d:
                with cols[i]:
                    st.metric(name, f"฿{d['price']}", f"{d['change']}%")
                    st.write(f"RSI: {d['rsi']}")
                    if d['rsi'] < 40: st.success("ช้อน KKP (Dime!)")
                    else: st.info("DCA SCB (InvX)")

    with t2:
        st.subheader("Value Investor Check (หน้า 8)")
        st.write("วิเคราะห์ความคุ้มค่าของเงินปันผลและสิทธิภาษี")
        
    with t3:
        st.subheader("DCA Calendar (หน้า 3)")
        st.write("วางแผนวันที่ดีที่สุดในการลงเงิน (เลี่ยงช่วง Window Dressing)")

def set_2_sniper_zing():
    """ชุดที่ 2: หุ้นซิ่ง (7, 9, 10, 11)"""
    st.header("🚀 ชุดที่ 2: Sniper Zing Hub (สแกน, วอลุ่ม, Backtest, ข่าว)")
    t1, t2, t3 = st.tabs(["🎯 สแกนซิ่ง & วอลุ่ม (7, 9)", "🧪 Backtest 1 ปี (10)", "📰 วิเคราะห์ข่าวรายตัว (11)"])
    
    with t1:
        st.subheader("Scanner: คัดตัวซิ่งล่วงหน้า")
        stocks = st.text_input("ระบุหุ้นซิ่งที่เฝ้า:", value="CPALL, WHA, TRUE").upper()
        for s in stocks.split(','):
            s = s.strip()
            d = get_analysis_data(s + ".BK")
            if d:
                with st.container():
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric(s, f"฿{d['price']}", f"{d['change']}%")
                    c2.metric("RSI Momentum", d['rsi'])
                    c3.metric("Volume Ratio", f"{d['vol_ratio']}x")
                    with c4:
                        if d['vol_ratio'] > 2: st.markdown("<span class='zing-tag'>🔥 SUPER ZING</span>", unsafe_allow_html=True)
                        if d['rsi'] < 40: st.markdown("<span class='buy-tag'>✅ ENTRY</span>", unsafe_allow_html=True)
                        st.write(f"Stop: {d['price']*0.97:.2f}")
                    st.divider()

    with t2:
        st.subheader("Backtest Lab (หน้า 10)")
        st.write("จำลองผลตอบแทนย้อนหลัง 1 ปี เมื่อซื้อที่ RSI ต่ำกว่าเกณฑ์")

    with t3:
        st.subheader("AI News Sentiment (หน้า 11)")
        news_input = st.text_area("วางข่าวล่าสุดที่นี่:")
        if st.button("วิเคราะห์ผลกระทบข่าว"):
            st.write(ai_news_impact(news_input, stocks))

def set_3_gold_sniper():
    """ชุดที่ 3: ทองคำ (5)"""
    st.header("🌕 ชุดที่ 3: Gold Sniper (ทองคำ)")
    d = get_analysis_data("GC=F")
    if d:
        st.metric("Gold Futures ($)", d['price'], f"{d['change']}%")
        st.write(f"RSI ทองคำ: {d['rsi']}")
    st.info("กลยุทธ์: เล่นทองคำเมื่อหุ้นไทยผันผวนจากการเมือง หรือ RSI หุ้นเข้าเขต Overbought")

def set_4_wealth_retirement():
    """ชุดที่ 4: พอร์ต & เกษียณ (2, 4) """
    st.header("🛡️ ชุดที่ 4: Wealth & Portfolio (พอร์ตปัจจุบัน & Titan)")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Portfolio ปัจจุบัน (หน้า 4)")
        st.write("สรุปยอดรวมสินทรัพย์ใน Dime! และ InnovestX")
    with col2:
        st.subheader("Titan เกษียณ (หน้า 2)")
        st.write("ตรวจสอบเป้าหมายเงินเก็บหลังเกษียณ")

# --- 4. Main Dispatcher (Sidebar Control) ---

with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>POLARIS</h1>", unsafe_allow_html=True)
    st.divider()
    choice = st.radio(
        "เลือกชุดปฏิบัติการ:",
        ["🚀 ชุด 2: หุ้นซิ่ง (7, 9, 10, 11)", 
         "⚖️ ชุด 1: หุ้นแกร่ง (1, 3, 6, 8)", 
         "🌕 ชุด 3: ทองคำ (5)", 
         "🛡️ ชุด 4: พอร์ต/เกษียณ (2, 4)"]
    )
    st.divider()
    st.caption(f"Engineered by P'Bo Sniper • {datetime.now().strftime('%H:%M')}")

# Dispatcher Logic
if choice == "🚀 ชุด 2: หุ้นซิ่ง (7, 9, 10, 11)":
    set_2_sniper_zing()
elif choice == "⚖️ ชุด 1: หุ้นแกร่ง (1, 3, 6, 8)":
    set_1_wealth_intelligence()
elif choice == "🛡️ ชุด 4: พอร์ต/เกษียณ (2, 4)":
    set_4_wealth_retirement()
else:
    set_3_gold_sniper()
