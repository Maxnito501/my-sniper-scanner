import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from datetime import date, datetime as dt
import google.generativeai as genai
import feedparser
import requests
import json
import time

# --- 1. การตั้งค่าพื้นฐาน (GLOBAL CONFIGURATION) ---
st.set_page_config(
    page_title="POLARIS: Grand Unified Hub",
    page_icon="🎯",
    layout="wide"
)

# การตั้งค่า AI (Gemini)
genai.configure(api_key="") # ระบบจะเติม API Key ให้เองในสภาพแวดล้อมจริง

# Custom CSS เพื่อความสวยงามระดับพรีเมียม (Zen & Sniper Style)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* การ์ดและ Metric */
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #e2e8f0;
    }
    .fund-card {
        background-color: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        margin-bottom: 10px;
    }
    .scb-line { border-left: 6px solid #6366f1; }
    .kkp-line { border-left: 6px solid #f59e0b; }
    .zing-tag { background: #fee2e2; color: #ef4444; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; border: 1px solid #ef4444; }
    .buy-tag { background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; border: 1px solid #166534; }
    .status-box { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 5px; }
    .positive-card { border-left: 5px solid #28a745; padding: 15px; background-color: #f0fff4; border-radius: 5px; margin-bottom: 10px; border: 1px solid #e2e8f0; }
    .negative-card { border-left: 5px solid #dc3545; padding: 15px; background-color: #fff5f5; border-radius: 5px; margin-bottom: 10px; border: 1px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันส่วนกลาง (SHARED UTILITIES) ---

@st.cache_data(ttl=600)
def get_data(ticker, period="1y"):
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return None

def calculate_indicators(df):
    close = df['Close']
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper_bb = sma20 + (std20 * 2)
    lower_bb = sma20 - (std20 * 2)
    pct_b = (close - lower_bb) / (upper_bb - lower_bb)
    
    return {
        "price": close.iloc[-1],
        "rsi": rsi.iloc[-1],
        "change": ((close.iloc[-1]/close.iloc[-2])-1)*100,
        "ma20": sma20.iloc[-1],
        "upper": upper_bb.iloc[-1],
        "lower": lower_bb.iloc[-1],
        "pct_b": pct_b.iloc[-1],
        "low_5d": close.iloc[-5:].min()
    }

# ฟังก์ชันส่ง LINE (หน้า 10)
def send_to_line(message):
    token = "XgyfEQh3dozGzEKKXVDUfWVBfBw+gX3yV976yTMnMnwPb+f9pHmytApjipzjXqhz/4IFB+qzMBpXx53NXTwaMMEZ+ctG6touSTIV4dXVEoWxoy5arbYVkkd2sxNCR0bX3GDc4A/XqjhnB38caUjyjQdB04t89/1O/w1cDnyilFU="
    uid = "Ua666a6ab22c5871d5cf4dc99d0f5045c"
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {"to": uid, "messages": [{"type": "text", "text": message}]}
    try: requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
    except: pass

# --- 3. ชุดที่ 1: WEALTH INTELLIGENCE (1, 3, 6, 8) ---

def set_1_wealth_intelligence():
    st.header("⚖️ ชุดที่ 1: Wealth Hub (หุ้นแกร่ง & ภาษี)")
    
    wealth_assets = {
        "Nasdaq 100": "^NDX", "S&P 500": "^GSPC", "SET 50": "^SET50.BK", 
        "Global Quality": "QUAL", "Semiconductor": "SOXX", "TISCO": "TISCO.BK"
    }
    
    c1, c2 = st.columns([2, 1])
    with c1:
        target_name = st.selectbox("🎯 เลือกสินทรัพย์สะสม", list(wealth_assets.keys()))
        ticker = wealth_assets[target_name]
    with c2:
        budget = st.number_input("💰 งบลงทุน (บาท)", value=10000, step=1000)

    df = get_data(ticker)
    if df is not None:
        tech = calculate_indicators(df)
        t1, t2, t3, t4 = st.tabs(["🚀 Sniper Scan (1&6)", "🏥 Doctor & Health (1&8)", "📅 DCA Oracle (3)", "🧮 Budget Plan"])
        
        with t1:
            st.metric(f"สถานะ {target_name}", f"RSI: {tech['rsi']:.2f}")
            is_rev = (tech['rsi'] < 45) and (tech['price'] > tech['low_5d'])
            if is_rev: st.success("🔥 สัญญาณกลับหัว! แนะนำ KKP (Dime!)")
            else: st.info("📉 DCA ปกติ แนะนำ SCB (InnovestX)")
            
        with t2:
            st.write("**💎 Buffett Scorecard (หน้า 8)**")
            st.info("P/E: 14.5 | ROE: 16.8% | Dividend Yield: 3.5%")
            cost = st.number_input("ต้นทุนของพี่โบ้", value=0.0)
            if cost > 0:
                diff = ((tech['price'] - cost) / cost) * 100
                st.write(f"กำไร/ขาดทุนปัจจุบัน: {diff:.2f}%")

        with t3:
            today = date.today().day
            st.subheader(f"วันที่ {today} - Oracle Analysis")
            pb = tech['pct_b'] * 100
            st.metric("ความแพง (Relative Price)", f"{pb:.1f}%")
            if pb < 20: st.success("OVERSOLD: จังหวะช้อนที่ดีที่สุด")
            elif pb > 80: st.error("OVERBOUGHT: ห้ามไล่ราคา")

        with t4:
            kkp_w = st.slider("สัดส่วน KKP (%)", 0, 100, 70 if tech['rsi'] < 45 else 50)
            st.metric("ยอดซื้อ KKP (Dime!)", f"฿{budget * (kkp_w/100):,.0f}")
            st.metric("ยอดซื้อ SCB (InvX)", f"฿{budget * ((100-kkp_w)/100):,.0f}")

# --- 4. ชุดที่ 2: SNIPER ZING HUB (7, 9, 10, 11) ---

def set_2_sniper_zing_hub():
    st.header("🚀 ชุดที่ 2: Sniper Zing Hub (หุ้นซิ่ง & ข่าว)")
    
    zing_pool = {
        "WHA.BK": "นิคมฯ", "TRUE.BK": "สื่อสาร", "CPALL.BK": "ค้าปลีก", 
        "DELTA.BK": "เทค", "GULF.BK": "พลังงาน", "TASCO.BK": "ก่อสร้าง"
    }
    
    t1, t2, t3, t4 = st.tabs(["🔥 Zing Scanner (7&9)", "🧪 Backtest Lab (10)", "📰 AI News Sniper (11)", "🧮 Dime! Calc"])
    
    with t1:
        st.subheader("ดักจับวอลุ่มเจ้าเข้า")
        data = yf.download(list(zing_pool.keys()), period="5d", interval="1d", progress=False)
        results = []
        for tick in zing_pool.keys():
            try:
                hist = data['Close'][tick]
                vol = data['Volume'][tick]
                chg = ((hist.iloc[-1]/hist.iloc[-2])-1)*100
                v_ratio = vol.iloc[-1] / vol.mean()
                status = "🔥 SUPER ZING" if v_ratio > 2.0 and chg > 1.5 else "🚀 MOMENTUM"
                results.append({"หุ้น": tick.replace(".BK",""), "ราคา": hist.iloc[-1], "Chg%": round(chg,2), "Vol Ratio": round(v_ratio,2), "สถานะ": status})
            except: continue
        st.dataframe(pd.DataFrame(results).sort_values("Vol Ratio", ascending=False), use_container_width=True, hide_index=True)
        
    with t2:
        bt_stock = st.text_input("ชื่อหุ้นทดสอบ", "WHA").upper()
        if st.button("รัน Backtest 1 ปี"):
            df_bt = get_data(bt_stock + ".BK")
            if df_bt is not None:
                ret = ((df_bt['Close'].iloc[-1]/df_bt['Close'].iloc[0])-1)*100
                st.metric(f"ผลตอบแทน {bt_stock}", f"{ret:.2f}%")
                st.line_chart(df_bt['Close'])
                send_to_line(f"Backtest {bt_stock}: กำไรสะสม {ret:.2f}% ครับพี่โบ้!")

    with t3:
        st.subheader("วิเคราะห์ข่าวด้วย AI")
        news_text = st.text_area("ก๊อปปี้ข่าวมาวางที่นี่:")
        if st.button("🔍 AI วิเคราะห์ด่วน"):
            model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
            res = model.generate_content(f"วิเคราะห์ข่าวหุ้น: {news_text} ให้คะแนน -10 ถึง 10 และแนะนำ ช้อน หรือ หมอบ")
            st.markdown(f"<div class='positive-card'>{res.text}</div>", unsafe_allow_html=True)

    with t4:
        c1, c2, c3 = st.columns(3)
        b_p = c1.number_input("ราคาซื้อ", value=10.0)
        s_p = c2.number_input("ราคาขาย", value=10.5)
        sh = c3.number_input("จำนวนหุ้น", value=1000, step=100)
        
        fees = (b_p + s_p) * sh * 0.00157 # ประมาณการค่าคอมฯ Dime!
        net = ((s_p - b_p) * sh) - fees
        st.metric("กำไรสุทธิ (Net Profit)", f"฿{net:,.2f}", f"หักค่าคอมฯ ฿{fees:.2f}")

# --- 5. การนำทาง (MAIN DISPATCHER) ---

def main():
    with st.sidebar:
        st.title("POLARIS v4.5")
        st.markdown("<p style='color:gray;'>Unified Commander</p>", unsafe_allow_html=True)
        st.divider()
        mode = st.radio("ชุดปฏิบัติการ", [
            "🚀 ชุดที่ 2: หุ้นซิ่ง Sniper",
            "⚖️ ชุดที่ 1: หุ้นแกร่ง & ภาษี",
            "🛡️ ชุดที่ 4: พอร์ต & เกษียณ",
            "🌕 ชุดที่ 3: ทองคำ Sniper"
        ])
        st.divider()
        st.caption(f"Update: {dt.now().strftime('%H:%M:%S')}")

    if "ชุดที่ 2" in mode:
        set_2_sniper_zing_hub()
    elif "ชุดที่ 1" in mode:
        set_1_wealth_intelligence()
    else:
        st.info("กำลังรอประกอบร่างชุดที่ 3 และ 4 ครับพี่โบ้!")

if __name__ == "__main__":
    main()
