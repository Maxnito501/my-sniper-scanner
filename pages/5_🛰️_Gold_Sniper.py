import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import requests

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Gold Sniper System", page_icon="🛰️", layout="wide")

st.title("🛰️ POLARIS: Gold Sniper (Calibration V5.7)")
st.markdown("""
**ระบบล่าค่าขนมทองคำ (โหมดแม่นยำสูง)**
* 🟢 **ไม้ 1:** เปิดเกมเมื่อย่อตัว
* 🟡 **ไม้ 2-3:** ถัวเฉลี่ยเมื่อผิดทาง
* 🎯 **เป้าหมาย:** ขายเมื่อกำไรเข้าเป้า (Hit & Run)
""")
st.write("---")

# --- 2. ระบบจัดการข้อมูล (Database & Fix) ---
DB_FILE = 'gold_data.json'

def load_data():
    # พยายามโหลดจากไฟล์
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                
                # 🛠️ FIX: ตรวจสอบและเติมค่าที่ขาด (Migration)
                # ถ้าไฟล์เก่าไม่มี key พวกนี้ ให้เติมค่าเริ่มต้นเข้าไป
                if 'accumulated_profit' not in data:
                    data['accumulated_profit'] = 0.0
                
                if 'vault' not in data:
                    data['vault'] = []
                    
                if 'portfolio' not in data:
                    data['portfolio'] = {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} for i in range(1, 6)}
                
                return data
        except: pass
    
    # ถ้าไม่มีไฟล์ หรือไฟล์เสีย ให้สร้างใหม่
    return {
        'portfolio': {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} for i in range(1, 6)},
        'vault': [],
        'accumulated_profit': 0.0
    }

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

if 'gold_data' not in st.session_state:
    st.session_state.gold_data = load_data()

# --- 3. ฟังก์ชันแจ้งเตือน (Audit Log) ---
def notify_action(action_type, wood_num, price, detail=""):
    msg = f"🛰️ **Gold Sniper Action**\n-----------------------\n⚡ **{action_type}** (ไม้ที่ {wood_num})\n💰 ราคา: {price:,.0f} บาท\n📝 {detail}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    
    if 'LINE_ACCESS_TOKEN' in st.secrets and 'LINE_USER_ID' in st.secrets:
        try:
            url = 'https://api.line.me/v2/bot/message/push'
            headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {st.secrets['LINE_ACCESS_TOKEN']}"}
            data = {'to': st.secrets['LINE_USER_ID'], 'messages': [{'type': 'text', 'text': msg.replace('*', '')}]}
            requests.post(url, headers=headers, json=data)
        except: pass

# --- 4. Sidebar ตั้งค่า ---
st.sidebar.header("⚙️ ตั้งค่าราคา (Price Control)")

# โหมดเลือกราคา
price_source = st.sidebar.radio("แหล่งที่มาราคา:", ["🤖 Auto (คำนวณจาก Spot)", "✍️ Manual (ระบุเองจากแอป)"])

current_thb_baht = 0.0 # ตัวแปรราคากลาง

if price_source == "🤖 Auto (คำนวณจาก Spot)":
    @st.cache_data(ttl=60) 
    def get_market_data():
        try:
            fx = yf.Ticker("THB=X").history(period="1d")['Close'].iloc[-1]
            df = yf.download("GC=F", period="5d", interval="1h", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            return float(fx), df
        except: return 34.50, None

    auto_fx, df_gold = get_market_data()
    
    st.sidebar.markdown("---")
    st.sidebar.caption("🔧 จูนสูตรคำนวณ")
    fx_rate = st.sidebar.number_input("ค่าเงินบาท", value=auto_fx, format="%.2f")
    premium = st.sidebar.number_input("Premium (ส่วนต่าง)", value=100.0, step=10.0)
    
    if df_gold is not None:
        current_usd = float(df_gold['Close'].iloc[-1])
        current_thb_baht = round(((current_usd * fx_rate * 0.473) + premium) / 50) * 50
        st.sidebar.success(f"ราคาคำนวณ: **{current_thb_baht:,.0f}**")
    else:
        st.sidebar.error("ดึงข้อมูลไม่ได้")

else:
    st.sidebar.markdown("---")
    st.sidebar.caption("✍️ กรอกราคาจริงที่เห็นในแอป")
    manual_price = st.sidebar.number_input("ราคาทอง (บาทละ)", value=40500, step=50, help="ดูราคา 'ซื้อออก' จากแอป GOLD NOW แล้วมากรอกที่นี่")
    current_thb_baht = manual_price
    df_gold = None

# ตั้งเป้ากำไร
st.sidebar.markdown("---")
spread_buffer = st.sidebar.number_input("Spread (ส่วนต่างซื้อ-ขาย)", value=50.0, step=10.0)
base_trade_size = st.sidebar.number_input("เงินต้นเริ่มแรก", value=10000, step=1000)
target_profit_amt = st.sidebar.number_input("เอากำไรกี่บาท/ไม้?", value=200, step=50)

# --- 5. ฟังก์ชันคำนวณกราฟ ---
def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

# --- 6. Main App Logic ---
advice = "พร้อมรับคำสั่ง (Manual Mode)"
bg_col, txt_col = "#f3f4f6", "black"
current_rsi = 0.0

if price_source == "🤖 Auto (คำนวณจาก Spot)" and df_gold is not None:
    df_gold = calculate_indicators(df_gold)
    current_rsi = df_gold['RSI'].iloc[-1]
    ema200 = df_gold['EMA200'].iloc[-1]
    last_close = df_gold['Close'].iloc[-1]
    
    if current_thb_baht > 0:
         if st.session_state.gold_data['portfolio']['1']['status'] == 'EMPTY':
             if last_close > ema200 and current_rsi <= 45: 
                 advice, bg_col = f"🚀 FIRE WOOD 1 (RSI {current_rsi:.0f})", "#dbeafe"
             elif current_rsi <= 30: 
                 advice, bg_col = f"🔫 SNIPER WOOD 1 (RSI {current_rsi:.0f})", "#bfdbfe"
             else:
                 advice, bg_col = f"⏳ WAIT (RSI {current_rsi:.0f})", "#f3f4f6"

# --- Dashboard Display ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("โหมดราคา", "Manual" if price_source == "✍️ Manual (ระบุเองจากแอป)" else "Auto")
c2.metric("RSI (1H)", f"{current_rsi:.1f}" if current_rsi > 0 else "-")
c3.metric("ราคาทองไทย (ที่ใช้)", f"{current_thb_baht:,.0f} ฿")

# 🛠️ FIX: ใช้ .get() เพื่อป้องกัน KeyError ในกรณีที่ session state ยังไม่อัปเดต
current_capital = base_trade_size + st.session_state.gold_data.get('accumulated_profit', 0.0)
c4.metric("เงินทุน (ทบต้น)", f"{current_capital:,.0f} ฿")

if price_source == "🤖 Auto (คำนวณจาก Spot)":
    st.markdown(f"<div style='background-color:{bg_col};padding:10px;border-radius:5px;text-align:center;'><b>🤖 {advice}</b></div>", unsafe_allow_html=True)

st.write("---")

# --- Operations Tabs ---
tab1, tab2, tab3 = st.tabs(["🔫 Sniper Board", "🧊 Vault", "📈 Chart"])

with tab1:
    st.subheader(f"🎯 เป้าหมาย: กำไร {target_profit_amt} บาท/ไม้")
    
    for i in range(1, 6):
        key = str(i)
        wood = st.session_state.gold_data['portfolio'][key]
        
        with st.container(border=True):
            col_id, col_info, col_btn = st.columns([1, 3, 2])
            with col_id:
                st.markdown(f"### 🪵 #{i}")
            with col_info:
                if wood['status'] == 'EMPTY':
                    st.caption("ว่าง (พร้อมยิง)")
                else:
                    curr_profit = (current_thb_baht - spread_buffer - wood['entry_price']) * wood['grams']
                    color_pl = "green" if curr_profit >= target_profit_amt else ("orange" if curr_profit > 0 else "red")
                    st.markdown(f"**ทุน:** {wood['entry_price']:.0f} | **กำไร:** :{color_pl}[{curr_profit:+.0f} ฿]")

            with col_btn:
                if wood['status'] == 'EMPTY':
                    prev_active = True if i == 1 else st.session_state.gold_data['portfolio'][str(i-1)]['status'] == 'ACTIVE'
                    if prev_active:
                        if st.button(f"🔴 ยิงไม้ {i}", key=f"buy_{i}", use_container_width=True):
                            st.session_state.gold_data['portfolio'][key] = {
                                'status': 'ACTIVE',
                                'entry_price': current_thb_baht,
                                'grams': current_capital / current_thb_baht,
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            save_data(st.session_state.gold_data)
                            notify_action("BUY (Manual)" if "Manual" in price_source else "BUY (Auto)", i, current_thb_baht)
                            st.rerun()
                else:
                    btn_label = f"💰 ขายรับตังค์" if curr_profit >= target_profit_amt else "ขาย (ยังไม่ถึงเป้า)"
                    btn_type = "primary" if curr_profit >= target_profit_amt else "secondary"
                    
                    if st.button(btn_label, key=f"sell_{i}", type=btn_type, use_container_width=True):
                        final_profit = (current_thb_baht - spread_buffer - wood['entry_price']) * wood['grams']
                        st.session_state.gold_data['vault'].append({
                            'wood': i,
                            'buy_price': wood['entry_price'],
                            'sell_price': current_thb_baht,
                            'profit': final_profit,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        # อัปเดตกำไรสะสม
                        if 'accumulated_profit' not in st.session_state.gold_data:
                            st.session_state.gold_data['accumulated_profit'] = 0.0
                        st.session_state.gold_data['accumulated_profit'] += final_profit
                        
                        st.session_state.gold_data['portfolio'][key] = {'status': 'EMPTY', 'entry_price': 0, 'grams': 0, 'date': None}
                        save_data(st.session_state.gold_data)
                        notify_action("SELL (Take Profit)", i, current_thb_baht, f"กำไร {final_profit:.0f} บาท")
                        st.success(f"ขายเรียบร้อย! กำไร {final_profit:+.0f} บาท")
                        st.rerun()

with tab2:
    st.subheader("🧊 ผลประกอบการ")
    vault_data = st.session_state.gold_data.get('vault', [])
    if vault_data:
        v_df = pd.DataFrame(vault_data)
        st.dataframe(v_df, use_container_width=True)
        total_profit = sum(d['profit'] for d in vault_data)
        st.metric("💰 กำไรสะสมทั้งหมด", f"{total_profit:,.0f} บาท")
        if st.button("🗑️ ล้างประวัติ"):
            st.session_state.gold_data['vault'] = []
            st.session_state.gold_data['accumulated_profit'] = 0
            save_data(st.session_state.gold_data)
            st.rerun()
    else:
        st.info("ยังไม่มีรายการขาย")

with tab3:
    if price_source == "🤖 Auto (คำนวณจาก Spot)" and df_gold is not None:
        st.subheader("📈 กราฟทองคำ (Spot USD)")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_gold.index, open=df_gold['Open'], high=df_gold['High'], low=df_gold['Low'], close=df_gold['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['EMA50'], name='EMA 50', line=dict(color='orange', width=1)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("โหมด Manual จะไม่แสดงกราฟ Real-time (เพราะคุณเป็นคนกำหนดราคาเอง)")
