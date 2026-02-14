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
    .buy-tag { background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

# --- Utility Functions (RSI & Data) ---
def get_stock_analysis(ticker):
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
        
        # Vol Ratio (เทียบเฉลี่ย 5 วัน)
        avg_vol = vol.iloc[-6:-1].mean()
        vol_ratio = vol.iloc[-1] / avg_vol if avg_vol > 0 else 0
        
        curr_price = float(close.iloc[-1])
        rsi_val = float(rsi.iloc[-1])
        vol_val = float(vol_ratio)
        
        # Sniper Logic
        advice = "Wait"
        if rsi_val < 35 and vol_val > 1.2: advice = "🔥 Strong Buy (Reversal)"
        elif 60 < rsi_val < 72 and vol_val > 2.0: advice = "🚀 Follow Buy (Momentum)"
        elif rsi_val > 75: advice = "🛑 Sell/Take Profit"
        elif vol_val > 2.5: advice = "⚡ Super Zing Entry"
        
        return {
            "price": round(curr_price, 2),
            "rsi": round(rsi_val, 2),
            "vol_ratio": round(vol_val, 2),
            "change": round(((curr_price - close.iloc[-2])/close.iloc[-2])*100, 2),
            "advice": advice
        }
    except: return None

# --- 2. Modules ตามชุดรบ ---

def zone_sniper_zing_hub():
    """ ชุดที่ 2: หุ้นซิ่ง (7, 9, 10, 11) """
    st.header("🚀 ชุดที่ 2: Sniper Zing Hub (7, 9, 10, 11)")
    t1, t2, t3 = st.tabs(["🎯 สแกนซิ่งล่วงหน้า (7 & 9)", "🧪 ผลย้อนหลัง 1 ปี (10)", "📰 ข่าวรายตัว AI (11)"])
    
    with t1:
        st.subheader("วิเคราะห์จุดเข้า-ออก และวอลุ่มความซิ่ง")
        targets = st.text_input("ระบุหุ้นที่เฝ้า (เช่น CPALL, WHA, TRUE, DELTA)", value="CPALL, WHA").upper()
        
        for s in targets.split(','):
            s = s.strip()
            data = get_stock_analysis(s + ".BK")
            if data:
                with st.container():
                    st.markdown(f"#### {s} - {data['advice']}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("ราคาปัจจุบัน", f"฿{data['price']}", f"{data['change']}%")
                    c2.metric("RSI (แรงส่ง)", data['rsi'])
                    c3.metric("Volume Ratio (เจ้าเข้า)", f"{data['vol_ratio']}x")
                    with c4:
                        st.write("**Sniper Guide:**")
                        if data['vol_ratio'] > 2: st.markdown("<span class='zing-tag'>🔥 SUPER ZING</span>", unsafe_allow_html=True)
                        if "Buy" in data['advice']: st.markdown("<span class='buy-tag'>✅ ENTRY POINT</span>", unsafe_allow_html=True)
                        st.write(f"คัทที่: {data['price']*0.97:.2f}")
                    st.divider()

def zone_wealth_intelligence():
    """ ชุดที่ 1: หุ้นแกร่ง & ภาษี (1, 3, 6, 8) """
    st.header("⚖️ ชุดที่ 1: Wealth Intelligence (1, 3, 6, 8)")
    st.info("หุ้นแกร่งสะสม | เช็กความคุ้ม | จังหวะ eDCA | วันที่ควรซื้อ")
    # (โค้ดส่วนหน้า 1, 3, 6, 8 จะอยู่ที่นี่)
    st.write("กำลังรอดึงข้อมูลกองทุน RMF...")

def zone_commodity_gold():
    """ ชุดที่ 3: ทองคำ (5) """
    st.header("🌕 ชุดที่ 3: Gold Sniper (5)")
    st.write("กลยุทธ์เล่นทองคำยามตลาดหุ้นนิ่ง")

def zone_wealth_retirement():
    """ ชุดที่ 4: ความมั่งคั่ง & พอร์ต (2, 4) """
    st.header("🛡️ ชุดที่ 4: Wealth & Portfolio (2, 4)")
    st.write("สินทรัพย์ปัจจุบัน และ แผนเกษียณ Titan")

# --- 3. Sidebar Menu ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>POLARIS v3.2</h1>", unsafe_allow_html=True)
    st.divider()
    selected_zone = st.radio(
        "โซนปฏิบัติการ:",
        [
            "🚀 ชุดที่ 2: หุ้นซิ่ง Sniper",
            "⚖️ ชุดที่ 1: หุ้นแกร่ง/ภาษี",
            "🌕 ชุดที่ 3: ทองคำ Sniper",
            "🛡️ ชุดที่ 4: พอร์ต/เกษียณ"
        ]
    )

# --- 4. Main Dispatcher ---
if selected_zone == "🚀 ชุดที่ 2: หุ้นซิ่ง Sniper":
    zone_sniper_zing_hub()
elif selected_zone == "⚖️ ชุดที่ 1: หุ้นแกร่ง/ภาษี":
    zone_wealth_intelligence()
elif selected_zone == "🛡️ ชุดที่ 4: พอร์ต/เกษียณ":
    zone_wealth_retirement()
else:
    zone_commodity_gold()
