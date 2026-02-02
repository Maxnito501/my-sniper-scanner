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

st.title("🛰️ POLARIS: Gold Sniper (Grid System V5.8)")
st.markdown("""
**ระบบเทรดทองคำแบบ Grid (ระยะห่างคงที่)**
* 🟢 **เข้าซื้อ:** เมื่อราคาลงมาถึงระยะที่ตั้งไว้ (เช่น ทุก -500 บาท)
* 🔴 **ขายทำกำไร:** เมื่อราคาดีดขึ้นถึงระยะที่ตั้งไว้ (เช่น +500 บาท)
""")
st.write("---")

# --- 2. ระบบจัดการข้อมูล ---
DB_FILE = 'gold_data.json'

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                if 'accumulated_profit' not in data: data['accumulated_profit'] = 0.0
                if 'vault' not in data: data['vault'] = []
                if 'portfolio' not in data: 
                    data['portfolio'] = {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} for i in range(1, 6)}
                return data
        except: pass
    
    return {
        'portfolio': {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} for i in range(1, 6)},
        'vault': [],
        'accumulated_profit': 0.0
    }

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

if 'gold_data' not in st.session_state:
    st.session_state.gold_data = load_data()

# --- 3. ฟังก์ชันแจ้งเตือน ---
def notify_action(action_type, wood_num, price, detail=""):
    msg = f"🛰️ **Gold Action**\n------------------\n⚡ **{action_type}** (ไม้ {wood_num})\n💰 ราคา: {price:,.0f} บาท\n📝 {detail}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    if 'LINE_ACCESS_TOKEN' in st.secrets:
        try:
            url = 'https://api.line.me/v2/bot/message/push'
            headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {st.secrets['LINE_ACCESS_TOKEN']}"}
            data = {'to': st.secrets['LINE_USER_ID'], 'messages': [{'type': 'text', 'text': msg.replace('*', '')}]}
            requests.post(url, headers=headers, json=data)
        except: pass

# --- 4. Sidebar ตั้งค่า (Grid Config) ---
st.sidebar.header("⚙️ ตั้งค่าราคา")
price_source = st.sidebar.radio("แหล่งที่มา:", ["🤖 Auto (Spot)", "✍️ Manual"])

current_thb_baht = 0.0 
if price_source == "🤖 Auto (Spot)":
    @st.cache_data(ttl=60) 
    def get_market_data():
        try:
            fx = yf.Ticker("THB=X").history(period="1d")['Close'].iloc[-1]
            df = yf.download("GC=F", period="5d", interval="1h", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            return float(fx), df
        except: return 34.50, None

    auto_fx, df_gold = get_market_data()
    st.sidebar.caption("🔧 จูนราคา")
    fx_rate = st.sidebar.number_input("USD/THB", value=auto_fx, format="%.2f")
    premium = st.sidebar.number_input("Premium (+)", value=100.0, step=10.0)
    
    if df_gold is not None:
        current_usd = float(df_gold['Close'].iloc[-1])
        current_thb_baht = round(((current_usd * fx_rate * 0.473) + premium) / 50) * 50
        st.sidebar.success(f"ราคา: **{current_thb_baht:,.0f}**")
else:
    manual_price = st.sidebar.number_input("ราคาทอง (บาทละ)", value=40500, step=50)
    current_thb_baht = manual_price
    df_gold = None

st.sidebar.markdown("---")
st.sidebar.header("📏 ตั้งค่าระยะ (Grid)")
# Config สำหรับระยะห่างและกำไร
gap_buy_1_2 = st.sidebar.number_input("ห่างไม้ 1->2 (ลงกี่บาทซื้อ)", value=500, step=100)
gap_buy_2_3 = st.sidebar.number_input("ห่างไม้ 2->3 (ลงกี่บาทซื้อ)", value=1000, step=100)
gap_profit = st.sidebar.number_input("กำไรขั้นต่ำ/ไม้ (บาท)", value=500, step=100)
spread_buffer = st.sidebar.number_input("เผื่อ Spread ขายคืน", value=50.0, step=10.0)

base_trade_size = st.sidebar.number_input("เงินต้นเริ่มแรก", value=10000, step=1000)

# --- 5. ฟังก์ชันคำนวณกราฟ ---
def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 6. วิเคราะห์สัญญาณ (Grid Logic) ---
def analyze_grid(df, current_price, portfolio):
    rsi = df['RSI'].iloc[-1] if df is not None else 50
    advice = "⏳ WAIT (ราคายังไม่เข้าเกณฑ์)"
    color = "#f3f4f6"
    text_color = "black"

    # เช็คสถานะการขาย (Take Profit)
    for i in range(1, 6):
        wood = portfolio[str(i)]
        if wood['status'] == 'ACTIVE':
            # เป้าขาย = ทุน + กำไรที่ตั้งไว้ + ค่าสเปรด
            target_sell = wood['entry_price'] + gap_profit + spread_buffer
            if current_price >= target_sell:
                return f"💰 SELL WOOD {i}! (ถึงเป้า {target_sell:,.0f})", "#dcfce7", "#166534"

    # เช็คสถานะการซื้อ (Buy Next Wood)
    # ไม้ 1: ดู RSI (เหมือนเดิม)
    if portfolio['1']['status'] == 'EMPTY':
        if rsi <= 45: 
            advice = f"🚀 FIRE WOOD 1 (RSI {rsi:.0f} สวย)"
            color = "#dbeafe"
        elif rsi <= 30:
            advice = f"💎 SNIPER WOOD 1 (RSI {rsi:.0f} ถูกมาก)"
            color = "#bfdbfe"
    else:
        # ไม้ 2-5: ดูระยะห่างราคา (Grid Gap)
        # หาไม้ล่าสุดที่ถืออยู่
        last_active_idx = 0
        for i in range(1, 6):
            if portfolio[str(i)]['status'] == 'ACTIVE': last_active_idx = i
        
        next_wood = last_active_idx + 1
        
        if next_wood <= 5:
            last_entry = portfolio[str(last_active_idx)]['entry_price']
            
            # กำหนดระยะห่างตามไม้
            gap_needed = gap_buy_1_2 if next_wood == 2 else gap_buy_2_3
            if next_wood >= 4: gap_needed = 1500 # ไม้ลึกๆ ห่างเยอะหน่อย
            
            target_buy = last_entry - gap_needed
            
            if current_price <= target_buy:
                advice = f"🛡️ FIRE WOOD {next_wood} (ราคาลงครบ {gap_needed} บาท)"
                color = "#fef9c3"
            else:
                advice = f"⏳ รอซื้อไม้ {next_wood} ที่ราคา {target_buy:,.0f} (ตอนนี้ {current_price:,.0f})"

    return advice, color, text_color

# --- 7. Main App ---
if price_source == "🤖 Auto (Spot)" and df_gold is not None:
    df_gold = calculate_indicators(df_gold)
    current_rsi = df_gold['RSI'].iloc[-1]
else:
    current_rsi = 0

advice, bg_col, txt_col = analyze_grid(df_gold, current_thb_baht, st.session_state.gold_data['portfolio'])

# Dashboard
c1, c2, c3, c4 = st.columns(4)
c1.metric("โหมด", "Manual" if "Manual" in price_source else "Auto")
c2.metric("RSI (1H)", f"{current_rsi:.1f}")
c3.metric("ราคาทองไทย", f"{current_thb_baht:,.0f} ฿")
current_capital = base_trade_size + st.session_state.gold_data.get('accumulated_profit', 0.0)
c4.metric("เงินทุน (ทบต้น)", f"{current_capital:,.0f} ฿")

st.markdown(f"<div style='background-color:{bg_col};padding:10px;border-radius:5px;text-align:center;color:{txt_col};'><b>🤖 {advice}</b></div>", unsafe_allow_html=True)
st.write("---")

# Operations Tabs
tab1, tab2 = st.tabs(["🔫 Sniper Board", "🧊 Vault"])

with tab1:
    st.subheader(f"🎯 เป้ากำไร: +{gap_profit} บาท/ไม้")
    for i in range(1, 6):
        key = str(i)
        wood = st.session_state.gold_data['portfolio'][key]
        
        with st.container(border=True):
            col_id, col_info, col_btn = st.columns([1, 3, 2])
            with col_id:
                st.markdown(f"### 🪵 #{i}")
            with col_info:
                if wood['status'] == 'EMPTY':
                    st.caption("ว่าง")
                    # โชว์เป้ารอซื้อ
                    if i > 1 and st.session_state.gold_data['portfolio'][str(i-1)]['status'] == 'ACTIVE':
                         last_p = st.session_state.gold_data['portfolio'][str(i-1)]['entry_price']
                         gap = gap_buy_1_2 if i==2 else (gap_buy_2_3 if i==3 else 1500)
                         st.info(f"🎯 รอช้อนที่: **{last_p - gap:,.0f}**")
                else:
                    target_sell = wood['entry_price'] + gap_profit + spread_buffer
                    curr_profit = (current_thb_baht - spread_buffer - wood['entry_price']) * wood['grams']
                    color_pl = "green" if current_thb_baht >= target_sell else "red"
                    st.markdown(f"ทุน: **{wood['entry_price']:.0f}** | เป้าขาย: **{target_sell:,.0f}**")
                    st.markdown(f"สถานะ: :{color_pl}[{curr_profit:+.0f} ฿]")

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
                            notify_action(f"BUY Wood {i}", i, current_thb_baht)
                            st.rerun()
                else:
                    target_sell = wood['entry_price'] + gap_profit + spread_buffer
                    btn_type = "primary" if current_thb_baht >= target_sell else "secondary"
                    if st.button(f"💰 ขายทำกำไร", key=f"sell_{i}", type=btn_type, use_container_width=True):
                        final_profit = (current_thb_baht - spread_buffer - wood['entry_price']) * wood['grams']
                        st.session_state.gold_data['vault'].append({
                            'wood': i, 'profit': final_profit, 'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        st.session_state.gold_data['accumulated_profit'] += final_profit
                        st.session_state.gold_data['portfolio'][key] = {'status': 'EMPTY', 'entry_price': 0, 'grams': 0, 'date': None}
                        save_data(st.session_state.gold_data)
                        notify_action(f"SELL Wood {i}", i, current_thb_baht, f"กำไร {final_profit:.0f}")
                        st.success(f"กำไร {final_profit:+.0f} บาท")
                        st.rerun()

with tab2:
    vault_data = st.session_state.gold_data.get('vault', [])
    if vault_data:
        st.dataframe(pd.DataFrame(vault_data), use_container_width=True)
        st.metric("กำไรสะสม", f"{sum(d['profit'] for d in vault_data):,.0f} ฿")
        if st.button("ล้างประวัติ"):
            st.session_state.gold_data['vault'] = []
            st.session_state.gold_data['accumulated_profit'] = 0
            save_data(st.session_state.gold_data)
            st.rerun()
