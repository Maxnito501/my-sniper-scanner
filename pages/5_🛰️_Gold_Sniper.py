import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Gold Sniper System", page_icon="🛰️", layout="wide")

st.title("🛰️ POLARIS: Gold Sniper")
st.markdown("**ระบบเทรดทองคำระยะสั้น (Short-term Trading System): แบ่งไม้-ไล่ราคา**")
st.write("---")

# --- 2. ตั้งค่าตัวแปร (Session State) ---
# เก็บสถานะพอร์ต 5 ไม้ (Wood 1-5)
if 'gold_portfolio' not in st.session_state:
    st.session_state.gold_portfolio = {
        i: {'status': 'EMPTY', 'entry_price': 0.0, 'grams': 0.0, 'date': None} 
        for i in range(1, 6)
    }

# เก็บประวัติกำไรเข้า Vault
if 'gold_vault' not in st.session_state:
    st.session_state.gold_vault = []

# --- 3. Sidebar ตั้งค่า ---
st.sidebar.header("⚙️ Sniper Settings")
fx_rate = st.sidebar.number_input("ค่าเงินบาท (USD/THB)", value=34.50, step=0.1)
gold_purity = st.sidebar.selectbox("ความบริสุทธิ์ทอง", ["99.99% (Spot)", "96.5% (ทองไทย)"])
trade_size = st.sidebar.number_input("วงเงินต่อไม้ (บาท)", value=10000, step=1000)

purity_factor = 0.965 if "96.5" in gold_purity else 1.0

# --- 4. ฟังก์ชันคำนวณ (Core Engine) ---
def usd_to_thb_gram(usd_price, exchange_rate, purity):
    # ทอง 1 Troy Ounce = 31.1035 กรัม
    price_per_gram_100 = (usd_price * exchange_rate) / 31.1035
    return price_per_gram_100 * purity

def calculate_indicators(df):
    # RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMA
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

@st.cache_data(ttl=300) # Cache 5 นาที
def get_gold_data():
    try:
        # ดึงกราฟรายชั่วโมง (1h) ย้อนหลัง 5 วัน เพื่อดูเทรนด์สั้น
        df = yf.download("GC=F", period="5d", interval="1h", progress=False)
        if len(df) == 0: return None
        
        # แก้ MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = calculate_indicators(df)
        return df
    except: return None

# --- 5. วิเคราะห์สัญญาณ (AI Signal) ---
def analyze_market(df, current_price, portfolio):
    rsi = df['RSI'].iloc[-1]
    ema50 = df['EMA50'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    
    advice = "⏳ WAIT (รอดูสถานการณ์)"
    color = "gray"

    # Logic: ไม้ 1 (เปิดเกม)
    if portfolio[1]['status'] == 'EMPTY':
        if current_price > ema200: # เทรนด์ขาขึ้น
            if rsi <= 45: # ย่อตัว
                advice = f"🚀 FIRE WOOD 1: ย่อตัวในขาขึ้น (RSI {rsi:.0f})"
                color = "green"
            else:
                advice = f"✋ WAIT WOOD 1: ราคายังสูง (RSI {rsi:.0f})"
        else:
            if rsi <= 30: # เด้งรีบาวด์
                advice = f"🔫 SNIPER SHOT: สวนเทรนด์ (RSI {rsi:.0f})"
                color = "orange"

    # Logic: ไม้ 2-5 (แก้เกม / ถัว)
    else:
        last_entry = 0
        # หาไม้ล่าสุดที่ยิงไป
        for i in range(1, 6):
            if portfolio[i]['status'] == 'ACTIVE':
                last_entry = portfolio[i]['entry_price']
        
        if last_entry > 0:
            if current_price < last_entry * 0.985: # ลงมา 1.5%
                advice = "🛡️ FIRE NEXT WOOD: ถัวเฉลี่ย (ราคาลง -1.5%)"
                color = "blue"
            elif current_price > last_entry * 1.02: # กำไร 2%
                advice = "💰 TAKE PROFIT: ขายทำกำไร (+2%)"
                color = "red"
                
    return advice, color, rsi

# --- 6. Main App Logic ---
df = get_gold_data()

if df is not None:
    current_usd = float(df['Close'].iloc[-1])
    current_thb = usd_to_thb_gram(current_usd, fx_rate, purity_factor)
    
    advice, signal_color, current_rsi = analyze_market(df, current_usd, st.session_state.gold_portfolio)

    # --- Dashboard ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gold Spot ($)", f"{current_usd:,.2f}")
    c2.metric("RSI (1H)", f"{current_rsi:.1f}")
    c3.metric("ราคาทองไทย (บาท/กรัม)", f"{current_thb:,.0f} ฿")
    
    # คำนวณมูลค่าพอร์ตปัจจุบัน
    total_grams = sum(p['grams'] for p in st.session_state.gold_portfolio.values())
    port_value = total_grams * current_thb
    c4.metric("มูลค่าพอร์ตปัจจุบัน", f"{port_value:,.0f} ฿")

    st.markdown(f"""
    <div style="background-color: {signal_color}; padding: 10px; border-radius: 5px; color: white; text-align: center; font-weight: bold;">
        🤖 AI SIGNAL: {advice}
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")

    # --- Operations Tabs ---
    tab1, tab2, tab3 = st.tabs(["🔫 Sniper Board (ยิงคำสั่ง)", "🧊 Vault (คลังสมบัติ)", "📈 Chart (กราฟ)"])

    with tab1:
        st.subheader("แผงควบคุมการยิง (5 ไม้)")
        
        for i in range(1, 6):
            col_id, col_status, col_action = st.columns([1, 2, 2])
            wood = st.session_state.gold_portfolio[i]
            
            with col_id:
                st.markdown(f"### 🪵 ไม้ที่ {i}")
            
            with col_status:
                if wood['status'] == 'EMPTY':
                    st.info("ว่าง (Ready)")
                else:
                    profit_loss = (current_thb - wood['entry_price']) * wood['grams']
                    pct = ((current_thb - wood['entry_price']) / wood['entry_price']) * 100
                    color = "green" if profit_loss > 0 else "red"
                    st.markdown(f"**ถือครอง:** {wood['grams']:.2f} กรัม")
                    st.markdown(f"**ทุน:** {wood['entry_price']:.0f} | **P/L:** :{color}[{profit_loss:+.0f} ฿ ({pct:+.2f}%)]")

            with col_action:
                if wood['status'] == 'EMPTY':
                    # ปุ่มซื้อ
                    if i == 1 or st.session_state.gold_portfolio[i-1]['status'] == 'ACTIVE':
                        if st.button(f"🔴 ยิงไม้ {i} (Buy)", key=f"buy_{i}"):
                            st.session_state.gold_portfolio[i] = {
                                'status': 'ACTIVE',
                                'entry_price': current_thb,
                                'grams': trade_size / current_thb,
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            st.rerun()
                    else:
                        st.caption("ต้องยิงไม้ก่อนหน้าก่อน")
                else:
                    # ปุ่มขาย
                    if st.button(f"🟢 ขายไม้ {i} (Sell)", key=f"sell_{i}"):
                        profit = (current_thb - wood['entry_price']) * wood['grams']
                        # บันทึกลง Vault
                        st.session_state.gold_vault.append({
                            'wood': i,
                            'buy_price': wood['entry_price'],
                            'sell_price': current_thb,
                            'profit': profit,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        # Reset ไม้
                        st.session_state.gold_portfolio[i] = {'status': 'EMPTY', 'entry_price': 0, 'grams': 0, 'date': None}
                        st.success(f"ขายทำกำไรเรียบร้อย! ({profit:+.0f} บาท)")
                        st.rerun()

    with tab2:
        st.subheader("🧊 รายการที่ปิดจ็อบแล้ว (History)")
        if st.session_state.gold_vault:
            vault_df = pd.DataFrame(st.session_state.gold_vault)
            st.dataframe(vault_df, use_container_width=True)
            
            total_profit = sum(item['profit'] for item in st.session_state.gold_vault)
            st.metric("💰 กำไรสะสมรวม", f"{total_profit:,.2f} บาท")
        else:
            st.info("ยังไม่มีรายการขายทำกำไร")

    with tab3:
        st.subheader("📈 กราฟทองคำรายชั่วโมง (XAU/USD)")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='blue', width=1)))
        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("ไม่สามารถดึงข้อมูลราคาทองคำได้ (ตลาดอาจปิด)")
