import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import google.generativeai as genai

# --- 1. การตั้งค่าพื้นฐานและธีม (Global Config) ---
st.set_page_config(
    page_title="POLARIS: Unified Command Center",
    page_icon="🎯",
    layout="wide"
)

# ปรับแต่ง CSS สไตล์วิศวกรโบ้ (Clean & Premium)
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .stMetric { background-color: white !important; border-radius: 12px !important; border: 1px solid #e2e8f0 !important; padding: 15px !important; }
    .strategy-note { background-color: #f1f5f9; padding: 15px; border-radius: 12px; border-left: 5px solid #334155; margin-bottom: 10px; }
    .fund-card { background: white; padding: 15px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    .zing-tag { background: #fee2e2; color: #ef4444; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

# --- Utility Functions (RSI & AI News) ---
def get_stock_data(ticker, period="3mo"):
    try:
        data = yf.download(ticker, period=period, interval="1d", progress=False)
        if data.empty: return None
        close = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
        vol = data['Volume'].iloc[:, 0] if isinstance(data['Volume'], pd.DataFrame) else data['Volume']
        
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Vol Ratio (เทียบเฉลี่ย 5 วัน)
        avg_vol = vol.iloc[-6:-1].mean()
        vol_ratio = vol.iloc[-1] / avg_vol if avg_vol > 0 else 0
        
        return {
            "price": round(float(close.iloc[-1]), 2),
            "rsi": round(float(rsi.iloc[-1]), 2),
            "vol_ratio": round(float(vol_ratio), 2),
            "change": round(((close.iloc[-1] - close.iloc[-2])/close.iloc[-2])*100, 2)
        }
    except: return None

def ai_news_analyzer(news_text, symbols):
    try:
        prompt = f"วิเคราะห์ข่าว: '{news_text}' ว่ามีผลบวกหรือลบต่อหุ้น {symbols} อย่างไร ให้คะแนน -10 ถึง 10 และแนะนำว่าควร ช้อน หรือ หมอบ สำหรับ Sniper"
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        response = model.generate_content(prompt)
        return response.text
    except: return "ไม่สามารถวิเคราะห์ข่าวได้ในขณะนี้"

# --- 2. Modules ตามชุดรบที่พี่โบ้วางแผน ---

def zone_sniper_zing_hub():
    """ ชุดที่ 2: หุ้นซิ่ง (7, 9, 10, 11) """
    st.header("🚀 Sniper Zing Hub: Momentum Action")
    t1, t2, t3 = st.tabs(["🎯 สแกนหาตัวซิ่ง (7 & 9)", "🧪 Backtest 1 ปี (10)", "📰 AI News Sniper (11)"])
    
    with t1:
        st.subheader("สแกนวอลุ่มและจุดเข้า-ออกรายวัน")
        target_zing = st.text_input("ระบุหุ้นที่เฝ้า (เช่น WHA, CPALL, TRUE)", value="WHA, CPALL").upper()
        # จำลองการดึงข้อมูล
        for s in target_zing.split(','):
            s = s.strip()
            data = get_stock_data(s + ".BK")
            if data:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(s, f"฿{data['price']}", f"{data['change']}%")
                c2.metric("RSI", data['rsi'])
                c3.metric("Vol Ratio", f"{data['vol_ratio']}x")
                with c4:
                    if data['vol_ratio'] > 2: st.markdown("<span class='zing-tag'>🔥 SUPER ZING</span>", unsafe_allow_html=True)
                    st.write(f"Entry: {data['price']*0.98:.2f}")
                    st.write(f"Target: {data['price']*1.05:.2f}")

    with t2:
        st.subheader("ทดสอบย้อนหลัง 1 ปี (Backtest Lab)")
        st.write("ดูผลตอบแทนย้อนหลังหากเข้าซื้อตามสัญญาณ RSI < 35")
        # โค้ด Backtest เดิมของพี่ที่ดึงข้อมูล yfinance ย้อนหลัง 1 ปี

    with t3:
        st.subheader("AI News Analyzer: วิเคราะห์ข่าวรายตัว")
        news = st.text_area("ก๊อปปี้ข่าวจากโซเชียลหรือเว็บข่าวมาวางที่นี่:")
        if st.button("วิเคราะห์แรงกระแทกข่าว"):
            res = ai_news_analyzer(news, target_zing)
            st.markdown(res)

def zone_wealth_intelligence():
    """ ชุดที่ 1: หุ้นแกร่ง & ภาษี (1, 3, 6, 8) """
    st.header("⚖️ Wealth Intelligence Hub")
    t1, t2 = st.tabs(["📈 สะสมหุ้นแกร่ง & eDCA (1, 6, 8)", "📅 ปฏิทิน DCA (3)"])
    
    with t1:
        st.subheader("จังหวะสะสมกองทุนและหุ้นพื้นฐาน")
        # โค้ด RSI Scan และการเลือกโบรกเกอร์ (Dime vs Innovest)
        st.info("ตรวจสอบความคุ้มค่า (Yield) และสิทธิภาษีก่อนเข้าสะสม")
        
    with t2:
        st.subheader("วันที่ควรเข้าซื้อ (DCA Planning)")
        st.write("เลือกวันที่เลี่ยงความผันผวนช่วงปลายเดือน")

def zone_commodity_gold():
    """ ชุดที่ 3: ทองคำ (5) """
    st.header("🌕 Gold Sniper Strategy")
    data = get_stock_data("GC=F")
    if data:
        st.metric("Gold Futures", f"${data['price']}", f"{data['change']}%")
    st.write("กลยุทธ์: เล่นทองคำเมื่อตลาดหุ้น Sideway หรือมีข่าวการเมืองวุ่นวาย")

def zone_wealth_retirement():
    """ ชุดที่ 4: ความมั่งคั่งและเกษียณ (2, 4) """
    st.header("🛡️ Wealth & Titan Portfolio")
    st.subheader("สินทรัพย์ปัจจุบันและแผนเกษียณ")
    # โค้ด Titan เดิมของพี่

# --- 3. ส่วนควบคุมเมนู (Sidebar) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>POLARIS v3.1</h1>", unsafe_allow_html=True)
    st.divider()
    selected_zone = st.radio(
        "โหมดการทำงาน:",
        [
            "🚀 หุ้นซิ่ง Sniper (ชุด 2)",
            "⚖️ หุ้นแกร่ง/ภาษี (ชุด 1)",
            "🛡️ พอร์ต/เกษียณ (ชุด 4)",
            "🌕 ทองคำ Sniper (ชุด 3)"
        ]
    )
    st.divider()
    st.caption(f"Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# --- 4. การแสดงผล (Dispatcher) ---
if selected_zone == "🚀 หุ้นซิ่ง Sniper (ชุด 2)":
    zone_sniper_zing_hub()
elif selected_zone == "⚖️ หุ้นแกร่ง/ภาษี (ชุด 1)":
    zone_wealth_intelligence()
elif selected_zone == "🛡️ พอร์ต/เกษียณ (ชุด 4)":
    zone_wealth_retirement()
else:
    zone_commodity_gold()
