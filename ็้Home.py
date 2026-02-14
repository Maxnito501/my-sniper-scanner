import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
from datetime import date, datetime as dt
import google.generativeai as genai
import feedparser
import requests
import json
import time
import os
import shutil
import numpy as np

# --- 1. GLOBAL CONFIGURATION & THEME ---
st.set_page_config(
    page_title="POLARIS: Grand Unified Hub v7.0",
    page_icon="🛡️",
    layout="wide"
)

# AI Configuration (Gemini)
genai.configure(api_key="") 

# Premium Styling: The "Bo Engineering" Signature Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* Advanced Card & Metric Styling */
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #e2e8f0;
    }
    .metric-card {
        background-color: #ffffff; border-radius: 15px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-top: 5px solid #1e3a8a;
    }
    .big-money { font-size: 2rem; font-weight: bold; color: #15803d; }
    .status-box { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 5px; }
    .gold-box { background-color: #fffbeb; padding: 20px; border-radius: 10px; border: 1px solid #fcd34d; text-align: center; }
    .strategy-note { background-color: #f1f5f9; padding: 15px; border-radius: 12px; border-left: 5px solid #334155; font-size: 0.9rem; }
    .positive-card { border-left: 5px solid #28a745; padding: 15px; background-color: #f0fff4; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA PERSISTENCE (Shared Databases) ---
DB_PORTFOLIO = 'my_portfolio.json'
DB_GOLD = 'gold_data.json'

def load_json(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return default_data

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Initialize Session States
if 'my_port_data' not in st.session_state:
    st.session_state.my_port_data = load_json(DB_PORTFOLIO, {
        "1. กองหลัง (Defensive)": [], "2. ตัวรุก (Aggressive)": [], 
        "3. หุ้นปันผล (Dividend)": [], "4. กองทุนภาษี (Tax Saving)": [], 
        "5. กองทุนระยะยาว (Long-term)": [], "6. ประกัน (Insurance)": []
    })

if 'gold_data' not in st.session_state:
    st.session_state.gold_data = load_json(DB_GOLD, {
        'portfolio': {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0} for i in range(1, 6)},
        'vault': [], 'accumulated_profit': 0.0
    })

# --- 3. SHARED ANALYTICS ENGINE ---

@st.cache_data(ttl=600)
def fetch_stock(ticker, period="1y", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return None

def get_tech_analysis(df):
    close = df['Close']
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    sma20 = close.rolling(20).mean()
    std = close.rolling(20).std()
    return {
        "price": close.iloc[-1], "rsi": rsi.iloc[-1], 
        "ma20": sma20.iloc[-1], "bb_low": sma20.iloc[-1] - (std.iloc[-1]*2),
        "low_5d": close.iloc[-5:].min(), "change": ((close.iloc[-1]/close.iloc[-2])-1)*100
    }

# --- 4. MODULES (The Battle Sets) ---

# --- ชุดที่ 1: WEALTH INTELLIGENCE (1, 3, 6, 8) ---
def set_1_wealth_intelligence():
    st.header("⚖️ ชุดที่ 1: Wealth Hub (หุ้นแกร่ง & ภาษี)")
    wealth_assets = {"Nasdaq 100": "^NDX", "S&P 500": "^GSPC", "SET 50": "^SET50.BK", "TISCO": "TISCO.BK", "CPALL": "CPALL.BK"}
    c1, c2 = st.columns([2, 1])
    with c1: target = st.selectbox("🎯 เลือกสินทรัพย์", list(wealth_assets.keys()))
    with c2: budget = st.number_input("💰 งบช้อน (บาท)", value=10000, step=1000)
    
    df = fetch_stock(wealth_assets[target])
    if df is not None:
        tech = get_tech_analysis(df)
        t1, t2, t3 = st.tabs(["🚀 Sniper Scan", "🏥 Health Check", "📅 DCA Oracle"])
        with t1:
            st.metric(f"RSI {target}", f"{tech['rsi']:.2f}")
            if tech['rsi'] < 40: st.success("🔥 จังหวะช้อน! แนะนำ KKP (Dime!)")
            else: st.info("📈 DCA ปกติ (InnovestX)")
        with t2:
            st.write("**💎 Buffett Quality Score**")
            st.write("P/E: 14.5 | Yield: 3.2% | ROE: 16% (Excellent)")
        with t3:
            today = date.today().day
            st.info(f"วันนี้วันที่ {today}: {'✅ วันของถูก' if today <= 10 else '⚠️ ระวัง Window Dressing'}")

# --- ชุดที่ 2: SNIPER ZING HUB (7, 9, 10, 11) ---
def set_2_sniper_zing_hub():
    st.header("🚀 ชุดที่ 2: Sniper Zing Hub (หุ้นซิ่ง & ข่าว)")
    zing_list = ["WHA.BK", "TRUE.BK", "CPALL.BK", "DELTA.BK", "GULF.BK"]
    t1, t2, t3 = st.tabs(["🔥 Zing Scanner", "🧪 Backtest 1Y", "📰 AI News Sniper"])
    with t1:
        data = yf.download(zing_list, period="5d", interval="1d", progress=False)
        res = []
        for t in zing_list:
            try:
                h = data['Close'][t]
                v = data['Volume'][t]
                v_ratio = v.iloc[-1] / v.mean()
                res.append({"Stock": t.replace(".BK",""), "Price": h.iloc[-1], "Vol Ratio": round(v_ratio,2), "Status": "🔥 ZING" if v_ratio > 2 else "Steady"})
            except: continue
        st.dataframe(pd.DataFrame(res).sort_values("Vol Ratio", ascending=False), use_container_width=True)
    with t2:
        bt = st.text_input("ระบุชื่อหุ้น", "WHA").upper()
        if st.button("🚀 Backtest"):
            df_bt = fetch_stock(bt+".BK")
            if df_bt is not None:
                ret = ((df_bt['Close'].iloc[-1]/df_bt['Close'].iloc[0])-1)*100
                st.metric("Total Return", f"{ret:.2f}%")
                st.line_chart(df_bt['Close'])
    with t3:
        news = st.text_area("วางข่าวที่นี่")
        if st.button("🔍 AI วิเคราะห์"):
            model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
            st.markdown(f"<div class='positive-card'>{model.generate_content(news).text}</div>", unsafe_allow_html=True)

# --- ชุดที่ 3: GOLD SNIPER (5) ---
def set_3_gold_sniper():
    st.header("🌕 ชุดที่ 3: Gold Sniper (Grid 5 Woods)")
    df_g = fetch_stock("GC=F", period="3mo", interval="1h")
    if df_g is not None:
        tech = get_tech_analysis(df_g)
        st.metric("Gold Spot ($)", f"{tech['price']:.2f}", f"{tech['change']:.2f}%")
        st.info(f"RSI: {tech['rsi']:.1f} | {'🔥 น่าช้อนสวน' if tech['rsi'] < 35 else '⏳ รอย่อ'}")
        fig = go.Figure(data=[go.Candlestick(x=df_g.index, open=df_g['Open'], high=df_g['High'], low=df_g['Low'], close=df_g['Close'])])
        fig.update_layout(height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# --- ชุดที่ 4: WEALTH & TITAN (2, 4) ---
def set_4_wealth_retirement():
    st.header("🛡️ ชุดที่ 4: Wealth & Titan Simulator (Inflation Adj.)")
    t1, t2, t3 = st.tabs(["📊 พอร์ตปัจจุบัน (หน้า 4)", "👴 Titan Simulator (หน้า 2)", "📝 แก้ไขรายการ"])
    
    # Calculate Wealth
    port_list = []
    investment_total = 0
    insurance_total = 0
    for cat, items in st.session_state.my_port_data.items():
        for item in items:
            if "ประกัน" in cat: insurance_total += item['value']
            else: 
                investment_total += item['value']
                port_list.append({"Category": cat, "Asset": item['name'], "Value": item['value']})
    
    total_net_worth = investment_total + insurance_total

    with t1:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><h4>ความมั่งคั่งสุทธิ</h4><div class="big-money">{total_net_worth:,.0f} ฿</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card" style="border-top-color:#10b981"><h4>พอร์ตลงทุน</h4><div class="big-money" style="color:#10b981">{investment_total:,.0f} ฿</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card" style="border-top-color:#f59e0b"><h4>หลักประกัน</h4><div class="big-money" style="color:#f59e0b">{insurance_total:,.0f} ฿</div></div>', unsafe_allow_html=True)
        
        if port_list:
            fig = px.sunburst(pd.DataFrame(port_list), path=['Category', 'Asset'], values='Value', color='Category')
            st.plotly_chart(fig, use_container_width=True)

    with t2:
        st.subheader("🚀 จำลองอนาคต & ค่าเงินเฟ้อ")
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            years_to_retire = st.number_input("ปีที่จะเกษียณ", value=9.75)
            target_sum = st.number_input("เป้าหมายเงินก้อน", value=10000000)
        with col_in2:
            salary = st.number_input("เงินเดือนปัจจุบัน", value=48780)
            gov_years = st.number_input("อายุราชการรวม", value=35.0)
        with col_in3:
            inflation = st.slider("เงินเฟ้อเฉลี่ย (%)", 0.0, 5.0, 3.0)
            exp_return = st.slider("ผลตอบแทนพอร์ต (%)", 1.0, 15.0, 7.0)

        # Simulation Logic
        months = int(years_to_retire * 12)
        sim_wealth = investment_total
        monthly_return = (exp_return / 100) / 12
        wealth_history = [sim_wealth]
        
        for _ in range(months):
            sim_wealth = (sim_wealth * (1 + monthly_return))
            wealth_history.append(sim_wealth)
        
        final_wealth_nom = sim_wealth
        inf_factor = (1 + inflation/100) ** years_to_retire
        final_wealth_real = final_wealth_nom / inf_factor
        
        st.divider()
        res1, res2 = st.columns(2)
        res1.metric("เงินก้อนวันเกษียณ (Nominal)", f"{final_wealth_nom/1000000:,.2f} ล้าน฿")
        res2.metric("มูลค่าจริง (หักเงินเฟ้อ)", f"{final_wealth_real/1000000:,.2f} ล้าน฿", delta_color="inverse")
        
        # Projection Chart
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(y=wealth_history, name="Nominal Value", line=dict(color="#2563eb", width=4)))
        st.plotly_chart(fig_proj, use_container_width=True)

    with t3:
        col_add, col_del = st.columns(2)
        with col_add:
            with st.form("add"):
                cat = st.selectbox("หมวดหมู่", list(st.session_state.my_port_data.keys()))
                name = st.text_input("ชื่อรายการ")
                val = st.number_input("มูลค่า", min_value=0)
                if st.form_submit_button("บันทึก"):
                    st.session_state.my_port_data[cat].append({"name": name, "value": val})
                    save_json(DB_PORTFOLIO, st.session_state.my_port_data); st.rerun()
        with col_del:
            cat_del = st.selectbox("หมวดที่จะลบ", list(st.session_state.my_port_data.keys()))
            items = [i['name'] for i in st.session_state.my_port_data[cat_del]]
            item_del = st.selectbox("เลือกรายการ", items if items else ["-"])
            if st.button("ลบรายการ"):
                st.session_state.my_port_data[cat_del] = [i for i in st.session_state.my_port_data[cat_del] if i['name'] != item_del]
                save_json(DB_PORTFOLIO, st.session_state.my_port_data); st.rerun()

# --- 5. MAIN DISPATCHER ---
def main():
    with st.sidebar:
        st.title("POLARIS v7.0 🏆")
        st.markdown("<p style='color:gray;'>The Grand Unified Command</p>", unsafe_allow_html=True)
        st.divider()
        mode = st.radio("ชุดปฏิบัติการ", [
            "🚀 ชุดที่ 2: หุ้นซิ่ง Sniper (7,9,10,11)",
            "⚖️ ชุดที่ 1: หุ้นแกร่ง & ภาษี (1,3,6,8)",
            "🌕 ชุดที่ 3: ทองคำ Sniper (V6.4)",
            "🛡️ ชุดที่ 4: พอร์ต & เกษียณ (2,4)"
        ], index=3)
        st.divider()
        st.caption(f"Engineered by P'Bo 50 | {dt.now().strftime('%H:%M:%S')}")

    if "ชุดที่ 4" in mode: set_4_wealth_retirement()
    elif "ชุดที่ 2" in mode: set_2_sniper_zing_hub()
    elif "ชุดที่ 1" in mode: set_1_wealth_intelligence()
    elif "ชุดที่ 3" in mode: set_3_gold_sniper()

if __name__ == "__main__":
    main()
