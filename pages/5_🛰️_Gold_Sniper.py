import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Gold Sniper System", page_icon="🛰️", layout="wide")

st.title("🛰️ POLARIS: Gold Sniper (Persistent)")
st.markdown("**ระบบเทรดทองคำระยะสั้น: เก็งกำไรกระแสเงินสด (Auto-Save)**")
st.write("---")

# --- 2. ระบบจัดการข้อมูล (Database) ---
DB_FILE = 'gold_data.json'

def load_data():
    """โหลดข้อมูลจากไฟล์ JSON ถ้าไม่มีให้สร้างใหม่"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except: pass
    
    # ค่าเริ่มต้น
    return {
        'portfolio': {str(i): {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} for i in range(1, 6)},
        'vault': []
    }

def save_data(data):
    """บันทึกข้อมูลลงไฟล์"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

# โหลดข้อมูลเข้า Session State
if 'gold_data' not in st.session_state:
    st.session_state.gold_data = load_data()

# --- 3. Sidebar ตั้งค่า ---
st.sidebar.header("⚙️ Sniper Settings")

# ดึงค่าเงินบาท Real-time
@st.cache_data(ttl=300)
def get_fx_rate():
    try:
        fx = yf.Ticker("THB=X").history(period="1d")['Close'].iloc[-1]
        return float(fx)
    except: return 34.50

auto_fx = get_fx_rate()
use_auto_fx = st.sidebar.checkbox("ใช้ค่าเงินบาท Real-time", value=True)
fx_rate = st.sidebar.number_input("ค่าเงินบาท (USD/THB)", value=auto_fx if use_auto_fx else 34.50, step=0.1)

gold_purity = st.sidebar.selectbox("ความบริสุทธิ์ทอง", ["96.5% (ทองไทย)", "99.99% (Spot)"])
trade_size = st.sidebar.number_input("วงเงินต่อไม้ (บาท)", value=10000, step=1000)

purity_factor = 0.965 if "96.5" in gold_purity else 1.0

# --- 4. ฟังก์ชันคำนวณ ---
def usd_to_thb_gram(usd_price, exchange_rate, purity):
    # 1 Troy Oz = 31.1035 Grams
    price_per_gram_100 = (usd_price * exchange_rate) / 31.1035
    return price_per_gram_100 * purity

def usd_to_thb_baht_weight(usd_price, exchange_rate, purity):
    # ทองคำแท่ง 1 บาท = 15.244 กรัม
    gram_price = usd_to_thb_gram(usd_price, exchange_rate, purity)
    return gram_price * 15.244

def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

@st.cache_data(ttl=60) # อัปเดตทุก 1 นาที
def get_gold_data():
    try:
        df = yf.download("GC=F", period="5d", interval="1h", progress=False)
        if len(df) == 0: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = calculate_indicators(df)
        return df
    except: return None

# --- 5. วิเคราะห์สัญญาณ ---
def analyze_market(df, current_price, portfolio):
    rsi = df['RSI'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    
    advice = "⏳ WAIT (รอดูสถานการณ์)"
    color = "#f3f4f6" # เทา
    text_color = "black"

    # Logic ไม้ 1
    if portfolio['1']['status'] == 'EMPTY':
        if current_price > ema200: 
            if rsi <= 45: 
                advice = f"🚀 FIRE WOOD 1: ย่อตัวในขาขึ้น (RSI {rsi:.0f})"
                color = "#dcfce7" # เขียวอ่อน
            else: 
                advice = f"✋ WAIT WOOD 1: ราคายังสูง (RSI {rsi:.0f})"
        else:
            if rsi <= 30: 
                advice = f"🔫 SNIPER SHOT: สวนเทรนด์ (RSI {rsi:.0f})"
                color = "#dbeafe" # ฟ้า
    else:
        # Logic ไม้แก้
        last_active = 0
        for i in range(1, 6):
            if portfolio[str(i)]['status'] == 'ACTIVE': last_active = portfolio[str(i)]['entry_price']
        
        if last_active > 0:
            if current_price < last_active * 0.985:
                advice = "🛡️ FIRE NEXT WOOD: ถัวเฉลี่ย (-1.5%)"
                color = "#fef9c3" # เหลือง
            elif current_price > last_active * 1.015:
                advice = "💰 TAKE PROFIT: ขายทำกำไร (+1.5%)"
                color = "#fee2e2" # แดงอ่อน

    return advice, color, text_color, rsi

# --- 6. Main App Logic ---
df = get_gold_data()

if df is not None:
    current_usd = float(df['Close'].iloc[-1])
    current_thb_gram = usd_to_thb_gram(current_usd, fx_rate, purity_factor)
    current_thb_baht = usd_to_thb_baht_weight(current_usd, fx_rate, purity_factor)
    
    advice, bg_col, txt_col, current_rsi = analyze_market(df, current_usd, st.session_state.gold_data['portfolio'])

    # Dashboard
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gold Spot ($)", f"{current_usd:,.2f}")
    c2.metric("RSI (1H)", f"{current_rsi:.1f}")
    c3.metric("ทองคำแท่ง (บาทละ)", f"{current_thb_baht:,.0f} ฿", help="ราคาประมาณการ (รวมค่ากำเหน็จอาจแพงกว่านี้)")
    
    total_grams = sum(p['grams'] for p in st.session_state.gold_data['portfolio'].values())
    port_value = total_grams * current_thb_gram
    c4.metric("มูลค่าพอร์ตปัจจุบัน", f"{port_value:,.0f} ฿")

    st.markdown(f"""
    <div style="background-color: {bg_col}; padding: 15px; border-radius: 10px; border: 1px solid #ccc; text-align: center; color: {txt_col};">
        <h3 style="margin:0;">🤖 {advice}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")

    # Operations Tabs
    tab1, tab2, tab3 = st.tabs(["🔫 Sniper Board", "🧊 Vault (ประวัติ)", "📈 Chart"])

    with tab1:
        st.subheader("แผงควบคุมการยิง (5 ไม้)")
        for i in range(1, 6):
            key = str(i)
            wood = st.session_state.gold_data['portfolio'][key]
            
            with st.container(border=True):
                col_id, col_info, col_btn = st.columns([1, 3, 2])
                
                with col_id:
                    st.markdown(f"### 🪵 #{i}")
                
                with col_info:
                    if wood['status'] == 'EMPTY':
                        st.caption("สถานะ: ว่าง (Ready)")
                    else:
                        profit_loss = (current_thb_gram - wood['entry_price']) * wood['grams']
                        pct = ((current_thb_gram - wood['entry_price']) / wood['entry_price']) * 100
                        color_pl = "green" if profit_loss > 0 else "red"
                        st.markdown(f"**ทุน:** {wood['entry_price']:.0f} บ./กรัม | **จำนวน:** {wood['grams']:.2f} กรัม")
                        st.markdown(f"**กำไร/ขาดทุน:** :{color_pl}[{profit_loss:+.0f} ฿ ({pct:+.2f}%)]")

                with col_btn:
                    if wood['status'] == 'EMPTY':
                        # เช็คเงื่อนไข: ต้องยิงเรียงลำดับ
                        prev_active = True if i == 1 else st.session_state.gold_data['portfolio'][str(i-1)]['status'] == 'ACTIVE'
                        if prev_active:
                            if st.button(f"🔴 ยิงไม้ {i} (Buy)", key=f"buy_{i}", use_container_width=True):
                                st.session_state.gold_data['portfolio'][key] = {
                                    'status': 'ACTIVE',
                                    'entry_price': current_thb_gram,
                                    'grams': trade_size / current_thb_gram,
                                    'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                save_data(st.session_state.gold_data)
                                st.rerun()
                        else:
                            st.button(f"🔒 ล็อก", key=f"lock_{i}", disabled=True, use_container_width=True)
                    else:
                        if st.button(f"🟢 ขายทำกำไร (Sell)", key=f"sell_{i}", type="primary", use_container_width=True):
                            profit = (current_thb_gram - wood['entry_price']) * wood['grams']
                            # Save to Vault
                            st.session_state.gold_data['vault'].append({
                                'wood': i,
                                'buy_price': wood['entry_price'],
                                'sell_price': current_thb_gram,
                                'profit': profit,
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            # Reset Wood
                            st.session_state.gold_data['portfolio'][key] = {'status': 'EMPTY', 'entry_price': 0, 'grams': 0, 'date': None}
                            save_data(st.session_state.gold_data)
                            st.success(f"ขายเรียบร้อย! กำไร {profit:+.0f} บาท")
                            st.rerun()

    with tab2:
        st.subheader("🧊 คลังสมบัติ (Trade History)")
        vault_data = st.session_state.gold_data.get('vault', [])
        if vault_data:
            v_df = pd.DataFrame(vault_data)
            st.dataframe(v_df, use_container_width=True)
            total_profit = sum(d['profit'] for d in vault_data)
            st.metric("💰 กำไรสะสมทั้งหมด", f"{total_profit:,.2f} บาท")
            
            if st.button("🗑️ ล้างประวัติ (Reset Vault)"):
                st.session_state.gold_data['vault'] = []
                save_data(st.session_state.gold_data)
                st.rerun()
        else:
            st.info("ยังไม่มีประวัติการขายทำกำไร")

    with tab3:
        st.subheader("📈 กราฟทองคำ (Real-time)")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='blue', width=1)))
        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("ไม่สามารถดึงข้อมูลราคาทองคำได้")
