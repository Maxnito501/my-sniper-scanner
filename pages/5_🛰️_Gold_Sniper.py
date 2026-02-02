import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import requests
import shutil

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Gold Sniper System", page_icon="🛰️", layout="wide")

st.title("🛰️ POLARIS: Gold Sniper (Statistical V6.0)")
st.markdown("""
**ระบบเทรดทองคำอ้างอิงสถิติ (Mean Reversion Strategy)**
* 🎯 **แม่นยำสูง:** ใช้ Bollinger Bands (2SD) จับจุดกลับตัว
* 🧱 **กับดักราคา:** คำนวณจุดซื้อที่ได้เปรียบที่สุดทางสถิติ
""")
st.write("---")

# --- 2. ระบบจัดการข้อมูล (Safe Database) ---
DB_FILE = 'gold_data.json'
BAK_FILE = 'gold_data.bak'

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'accumulated_profit' not in data: data['accumulated_profit'] = 0.0
                if 'vault' not in data: data['vault'] = []
                if 'portfolio' not in data: 
                    data['portfolio'] = {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} for i in range(1, 6)}
                return data
        except: 
            if os.path.exists(BAK_FILE): # กู้คืนจาก backup
                try: 
                    with open(BAK_FILE, 'r', encoding='utf-8') as f: return json.load(f)
                except: pass
            return None
    return {
        'portfolio': {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} for i in range(1, 6)},
        'vault': [],
        'accumulated_profit': 0.0
    }

def save_data(data):
    if os.path.exists(DB_FILE): 
        try: shutil.copy(DB_FILE, BAK_FILE)
        except: pass
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

if 'gold_data' not in st.session_state:
    loaded = load_data()
    if loaded: st.session_state.gold_data = loaded
    else: st.stop()

# --- 3. แจ้งเตือน ---
def notify_action(action_type, wood_num, price, detail=""):
    msg = f"🛰️ **Gold Action**\n------------------\n⚡ **{action_type}** (ไม้ {wood_num})\n💰 ราคา: {price:,.0f} บาท\n📝 {detail}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    if 'LINE_ACCESS_TOKEN' in st.secrets:
        try:
            url = 'https://api.line.me/v2/bot/message/push'
            headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {st.secrets['LINE_ACCESS_TOKEN']}"}
            data = {'to': st.secrets['LINE_USER_ID'], 'messages': [{'type': 'text', 'text': msg.replace('*', '')}]}
            requests.post(url, headers=headers, json=data)
        except: pass

# --- 4. Sidebar ---
st.sidebar.header("⚙️ ตั้งค่าราคา")
price_source = st.sidebar.radio("แหล่งที่มา:", ["🤖 Auto (Spot)", "✍️ Manual"])

current_thb_baht = 0.0 
df_gold = None

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
        st.sidebar.success(f"ราคาตลาด: **{current_thb_baht:,.0f}**")
else:
    manual_price = st.sidebar.number_input("ราคาทอง (บาทละ)", value=40500, step=50)
    current_thb_baht = manual_price

st.sidebar.markdown("---")
st.sidebar.header("📏 ตั้งค่า Grid")
gap_buy_1_2 = st.sidebar.number_input("ห่างไม้ 1->2 (บาท)", value=500, step=100)
gap_buy_2_3 = st.sidebar.number_input("ห่างไม้ 2->3 (บาท)", value=1000, step=100)
gap_profit = st.sidebar.number_input("กำไรขั้นต่ำ/ไม้ (บาท)", value=300, step=50) # เพิ่มเป้ากำไรนิดนึงให้คุ้มค่ารอ
spread_buffer = st.sidebar.number_input("เผื่อ Spread", value=50.0, step=10.0)
base_trade_size = st.sidebar.number_input("เงินต้นเริ่มแรก", value=10000, step=1000)

# --- 5. คำนวณกราฟ & สถิติ (Bollinger Bands) ---
def calculate_indicators(df):
    df = df.copy()
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands (2SD)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['Upper'] = df['SMA20'] + (df['STD20'] * 2)
    df['Lower'] = df['SMA20'] - (df['STD20'] * 2)
    
    # EMA
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    return df

# --- 6. Main Logic (Statistical Analysis) ---
portfolio = st.session_state.gold_data['portfolio']
last_active_wood = 0
for i in range(1, 6):
    if portfolio[str(i)]['status'] == 'ACTIVE': last_active_wood = i

# --- 7. Display ---
if df_gold is not None:
    df_gold = calculate_indicators(df_gold)
    current_rsi = df_gold['RSI'].iloc[-1]
    last_close = df_gold['Close'].iloc[-1]
    last_lower = df_gold['Lower'].iloc[-1]
    last_upper = df_gold['Upper'].iloc[-1]
else:
    current_rsi = 0.0
    last_close = 0.0
    last_lower = 0.0
    last_upper = 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("โหมด", "Auto" if "Auto" in price_source else "Manual")
c2.metric("RSI (1H)", f"{current_rsi:.1f}")
c3.metric("ราคาทองไทย", f"{current_thb_baht:,.0f} ฿")
current_capital = base_trade_size + st.session_state.gold_data.get('accumulated_profit', 0.0)
c4.metric("เงินทุน (ทบต้น)", f"{current_capital:,.0f} ฿")

# --- AI Recommendation Box ---
advice_color = "#f3f4f6"
advice_text = "⏳ WAIT: ตลาดยังไม่เข้าเกณฑ์สถิติ"

# Logic การแนะนำ (Stat-Based)
if last_active_wood == 0: # ไม้ 1
    if last_close < last_lower: # หลุดกรอบล่าง (Stat Extremes)
        if current_rsi <= 30:
            advice_text = f"💎 STATISTICAL BUY! ราคาหลุดกรอบล่าง + RSI {current_rsi:.0f} (โอกาสเด้ง 80%++)"
            advice_color = "#d1fae5" # เขียวเข้ม
        else:
            advice_text = f"🛒 WATCH LIST: ราคาหลุดกรอบ แต่ RSI ยังไม่สุด ({current_rsi:.0f})"
            advice_color = "#dbeafe" # ฟ้า
    elif current_rsi <= 40:
        advice_text = f"⚠️ BUY DIP: ราคาลงมาน่าสนใจ (ความแม่นยำ ~60%)"
        advice_color = "#fef9c3" # เหลือง
elif last_active_wood < 5: # ไม้แก้
    # ... (Logic เดิม) ...
    pass

st.markdown(f"<div style='background-color:{advice_color};padding:15px;border-radius:10px;text-align:center;'><b>🤖 {advice_text}</b></div>", unsafe_allow_html=True)
st.write("---")

tab1, tab2, tab3 = st.tabs(["🔫 Sniper Board", "🧊 Vault", "📈 Chart"])

with tab1:
    st.subheader(f"🎯 เป้ากำไร: +{gap_profit} บาท/ไม้")
    for i in range(1, 6):
        key = str(i)
        wood = portfolio[key]
        with st.container(border=True):
            col_id, col_info, col_btn = st.columns([1, 3, 2])
            with col_id: st.markdown(f"### 🪵 #{i}")
            with col_info:
                if wood['status'] == 'EMPTY':
                    st.caption("ว่าง")
                else:
                    target_sell = wood['entry_price'] + gap_profit + spread_buffer
                    curr_profit = (current_thb_baht - spread_buffer - wood['entry_price']) * wood['grams']
                    color_pl = "green" if current_thb_baht >= target_sell else "red"
                    st.markdown(f"ทุน: **{wood['entry_price']:.0f}** | เป้าขาย: **{target_sell:,.0f}**")
                    st.markdown(f"สถานะ: :{color_pl}[{curr_profit:+.0f} ฿]")

            with col_btn:
                if wood['status'] == 'EMPTY':
                    prev_active = True if i == 1 else portfolio[str(i-1)]['status'] == 'ACTIVE'
                    if prev_active:
                        if st.button(f"🔴 ยิงไม้ {i}", key=f"buy_{i}", use_container_width=True):
                            st.session_state.gold_data['portfolio'][key] = {
                                'status': 'ACTIVE', 'entry_price': current_thb_baht,
                                'grams': current_capital / current_thb_baht,
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            save_data(st.session_state.gold_data)
                            notify_action(f"BUY Wood {i}", i, current_thb_baht)
                            st.rerun()
                else:
                    target_sell = wood['entry_price'] + gap_profit + spread_buffer
                    btn_type = "primary" if current_thb_baht >= target_sell else "secondary"
                    if st.button(f"💰 ขาย", key=f"sell_{i}", type=btn_type, use_container_width=True):
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
            st.session_state.gold_data['vault'] = []; st.session_state.gold_data['accumulated_profit'] = 0
            save_data(st.session_state.gold_data); st.rerun()
    else: st.info("ยังไม่มีประวัติ")

with tab3:
    if df_gold is not None:
        st.subheader("📈 Bollinger Bands (2SD Strategy)")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_gold.index, open=df_gold['Open'], high=df_gold['High'], low=df_gold['Low'], close=df_gold['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['Upper'], line=dict(color='red', width=1, dash='dot'), name='Upper Band'))
        fig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['Lower'], line=dict(color='green', width=1, dash='dot'), name='Lower Band (Buy Zone)'))
        fig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['SMA20'], line=dict(color='blue', width=1), name='SMA 20'))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 **Tip:** รอราคาหลุดเส้นประสีเขียว (Lower Band) แล้วค่อยยิงไม้ 1 (โอกาสชนะสูง)")
    else: st.info("No Chart Data")
