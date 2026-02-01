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

st.title("🛰️ POLARIS: Gold Sniper (Full Log V5.6)")
st.markdown("""
**ระบบล่าค่าขนมทองคำ: เป้าหมาย 200-300 บาท/สัปดาห์**
* 🟢 **ไม้ 1:** เปิดเกมเมื่อย่อตัว
* 🟡 **ไม้ 2-3:** ถัวเฉลี่ยเมื่อผิดทาง
* 🎯 **เป้าหมาย:** ขายเมื่อกำไรเข้าเป้า (Hit & Run)
""")
st.write("---")

# --- 2. ระบบจัดการข้อมูล (Database) ---
DB_FILE = 'gold_data.json'

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: return json.load(f)
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

# --- 3. ฟังก์ชันแจ้งเตือน (Audit Log) ---
def notify_action(action_type, wood_num, price, detail=""):
    """ส่งแจ้งเตือนเมื่อมีการกดปุ่มซื้อขาย"""
    msg = f"🛰️ **Gold Sniper Action**\n"
    msg += f"-----------------------\n"
    msg += f"⚡ **{action_type}** (ไม้ที่ {wood_num})\n"
    msg += f"💰 ราคา: {price:,.0f} บาท\n"
    msg += f"📝 {detail}\n"
    msg += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    
    # 1. ส่ง LINE
    if 'LINE_ACCESS_TOKEN' in st.secrets and 'LINE_USER_ID' in st.secrets:
        try:
            url = 'https://api.line.me/v2/bot/message/push'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {st.secrets['LINE_ACCESS_TOKEN']}"
            }
            data = {
                'to': st.secrets['LINE_USER_ID'],
                'messages': [{'type': 'text', 'text': msg.replace('*', '')}]
            }
            requests.post(url, headers=headers, json=data)
        except: pass

    # 2. ส่ง Telegram
    if 'telegram_token' in st.secrets and 'telegram_chat_id' in st.secrets:
        try:
            tg_url = f"https://api.telegram.org/bot{st.secrets['telegram_token']}/sendMessage"
            requests.post(tg_url, json={
                "chat_id": st.secrets['telegram_chat_id'], 
                "text": msg, 
                "parse_mode": "Markdown"
            })
        except: pass

# --- 4. Sidebar ตั้งค่า ---
st.sidebar.header("⚙️ ตั้งค่าเป้าหมาย (Profit Config)")

@st.cache_data(ttl=300)
def get_fx_rate():
    try: return float(yf.Ticker("THB=X").history(period="1d")['Close'].iloc[-1])
    except: return 34.50

auto_fx = get_fx_rate()
use_auto_fx = st.sidebar.checkbox("Auto FX Rate", value=True)
fx_rate = st.sidebar.number_input("ค่าเงินบาท (USD/THB)", value=auto_fx if use_auto_fx else 34.50, step=0.1)

st.sidebar.markdown("---")
st.sidebar.caption("🔧 จูนราคาให้ตรงแอปเป๋าตัง/GOLD NOW")
premium = st.sidebar.number_input("ส่วนต่างราคา (Premium)", value=100.0, step=10.0)
spread_buffer = st.sidebar.number_input("เผื่อส่วนต่างซื้อ-ขาย (Spread)", value=50.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.caption("🎯 เป้าหมายค่าขนม")
base_trade_size = st.sidebar.number_input("เงินต้นเริ่มแรก (บาท)", value=10000, step=1000)
target_profit_amt = st.sidebar.number_input("เอากำไรกี่บาท/ไม้?", value=200, step=50)

# --- 5. ฟังก์ชันคำนวณ ---
def calculate_thai_gold_price(usd_price, exchange_rate, premium_add):
    theoretical_price = (usd_price * exchange_rate * 0.473)
    final_price = theoretical_price + premium_add
    return round(final_price / 50) * 50

def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

@st.cache_data(ttl=60)
def get_gold_data():
    try:
        df = yf.download("GC=F", period="5d", interval="1h", progress=False)
        if len(df) == 0: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = calculate_indicators(df)
        return df
    except: return None

# --- 6. วิเคราะห์สัญญาณ ---
def analyze_market(df, current_price, portfolio):
    rsi = df['RSI'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    
    advice = "⏳ WAIT (รอดูสถานการณ์)"
    color = "#f3f4f6"
    text_color = "black"

    for i in range(1, 6):
        wood = portfolio[str(i)]
        if wood['status'] == 'ACTIVE':
            target_sell_price = ((wood['entry_price'] * wood['grams']) + target_profit_amt) / wood['grams'] + spread_buffer
            if current_price >= target_sell_price:
                return f"💰 SELL WOOD {i}! (กำไรทะลุเป้า)", "#dcfce7", "#166534", rsi

    if portfolio['1']['status'] == 'EMPTY':
        if current_price > ema200 and rsi <= 45: 
            advice = f"🚀 FIRE WOOD 1 (RSI {rsi:.0f})"
            color = "#dbeafe"
        elif rsi <= 30: 
            advice = f"🔫 SNIPER WOOD 1 (RSI {rsi:.0f})"
            color = "#bfdbfe"
    else:
        next_w = 0
        for i in range(1, 6):
            if portfolio[str(i)]['status'] == 'EMPTY':
                next_w = i
                break
        
        if next_w > 1:
            last_price = portfolio[str(next_w-1)]['entry_price']
            if current_price < last_price * 0.99:
                advice = f"🛡️ FIRE WOOD {next_w} (ราคาลงมาสวย)"
                color = "#fef9c3"

    return advice, color, text_color, rsi

# --- 7. Main App Logic ---
df = get_gold_data()

if df is not None:
    current_usd = float(df['Close'].iloc[-1])
    current_thb_baht = calculate_thai_gold_price(current_usd, fx_rate, premium)
    
    advice, bg_col, txt_col, current_rsi = analyze_market(df, current_thb_baht, st.session_state.gold_data['portfolio'])

    # Dashboard
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gold Spot", f"${current_usd:,.2f}")
    c2.metric("RSI (1H)", f"{current_rsi:.1f}")
    c3.metric("ราคาทองไทย", f"{current_thb_baht:,.0f} ฿")
    
    current_capital = base_trade_size + st.session_state.gold_data['accumulated_profit']
    c4.metric("เงินทุน (ทบต้น)", f"{current_capital:,.0f} ฿")

    st.markdown(f"""
    <div style="background-color: {bg_col}; padding: 10px; border-radius: 5px; color: {txt_col}; text-align: center; font-weight: bold;">
        🤖 {advice}
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")

    # Operations
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
                            if st.button(f"🔴 ซื้อ (Buy)", key=f"buy_{i}", use_container_width=True):
                                # Save Logic
                                st.session_state.gold_data['portfolio'][key] = {
                                    'status': 'ACTIVE',
                                    'entry_price': current_thb_baht,
                                    'grams': current_capital / current_thb_baht,
                                    'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                save_data(st.session_state.gold_data)
                                # Notify
                                notify_action("BUY (เข้าซื้อ)", i, current_thb_baht, f"ใช้ทุน {current_capital:,.0f} บาท")
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
                            st.session_state.gold_data['accumulated_profit'] += final_profit
                            st.session_state.gold_data['portfolio'][key] = {'status': 'EMPTY', 'entry_price': 0, 'grams': 0, 'date': None}
                            save_data(st.session_state.gold_data)
                            
                            # Notify
                            notify_action("SELL (ขายทำกำไร)", i, current_thb_baht, f"กำไรเข้าเป้า +{final_profit:,.0f} บาท")
                            
                            st.success(f"เข้าเป้า! กำไร {final_profit:+.0f} บาท")
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
        st.subheader("📈 กราฟทองคำ")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50', line=dict(color='orange', width=1)))
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("ไม่สามารถดึงข้อมูลราคาทองคำได้")
