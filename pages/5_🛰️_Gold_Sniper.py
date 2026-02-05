import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json
import os
import requests
import shutil

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Gold Sniper System", page_icon="🛰️", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .gold-box { background-color: #fffbeb; padding: 20px; border-radius: 10px; border: 1px solid #fcd34d; text-align: center; }
    .sig-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; text-align: center; font-weight: bold; font-size: 1.1rem; }
    .buy-sig { background-color: #dcfce7; color: #166534; border: 1px solid #166534; }
    .sell-sig { background-color: #fee2e2; color: #991b1b; border: 1px solid #991b1b; }
    .wait-sig { background-color: #f3f4f6; color: #374151; border: 1px solid #6b7280; }
    .hold-sig { background-color: #e0f2fe; color: #1e40af; border: 1px solid #1e40af; }
    
    .footer { text-align: center; color: #94a3b8; font-size: 0.9rem; margin-top: 50px; border-top: 1px dashed #cbd5e1; padding-top: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("🛰️ POLARIS: Gold Sniper (RSI Chart V6.3 Fixed)")
st.markdown("**ระบบเทรดทองคำส่วนตัว: เพิ่มกราฟ RSI เพื่อจับจังหวะด้วยตา**")
st.write("---")

# --- 2. ระบบจัดการข้อมูล ---
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
            if os.path.exists(BAK_FILE):
                try: with open(BAK_FILE, 'r', encoding='utf-8') as f: return json.load(f)
                except: pass
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
    st.session_state.gold_data = load_data()

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
    if 'telegram_token' in st.secrets:
        try:
            tg_url = f"https://api.telegram.org/bot{st.secrets['telegram_token']}/sendMessage"
            requests.post(tg_url, json={"chat_id": st.secrets['telegram_chat_id'], "text": msg, "parse_mode": "Markdown"})
        except: pass

# --- 4. ฟังก์ชันคำนวณและดึงข้อมูล ---
def calculate_indicators(df):
    df = df.copy() # ป้องกัน SettingWithCopyWarning
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

def find_support_resistance(df):
    recent_low = df['Low'].tail(20).min()
    recent_high = df['High'].tail(20).max()
    return recent_low, recent_high

# เปลี่ยนชื่อฟังก์ชันเพื่อ Clear Cache
@st.cache_data(ttl=60)
def get_market_data_v2(): 
    try:
        fx = yf.Ticker("THB=X").history(period="1d")['Close'].iloc[-1]
        df = yf.download("GC=F", period="3mo", interval="1h", progress=False)
        
        # จัดการ MultiIndex
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
            
        if len(df) > 0: 
            df = calculate_indicators(df)
            
        return float(fx), df
    except: return 34.50, None

# --- 5. Sidebar ตั้งค่า ---
st.sidebar.header("⚙️ ตั้งค่าราคา")
price_source = st.sidebar.radio("แหล่งที่มา:", ["🤖 Auto (Spot)", "✍️ Manual (ระบุเอง)"])

auto_fx, df_gold = get_market_data_v2() # เรียกฟังก์ชันใหม่
current_thb_baht = 0.0 
current_rsi = 0.0
support_usd, resistance_usd = 0.0, 0.0

if price_source == "🤖 Auto (Spot)":
    st.sidebar.caption("🔧 จูนราคาให้ตรงแอป")
    fx_rate = st.sidebar.number_input("USD/THB", value=auto_fx, format="%.2f")
    premium = st.sidebar.number_input("Premium (+)", value=100.0, step=10.0)
    
    if df_gold is not None and 'RSI' in df_gold.columns: # เช็คก่อนว่ามี RSI ไหม
        current_usd = float(df_gold['Close'].iloc[-1])
        current_thb_baht = round(((current_usd * fx_rate * 0.473) + premium) / 50) * 50
        current_rsi = df_gold['RSI'].iloc[-1]
        support_usd, resistance_usd = find_support_resistance(df_gold)
        st.sidebar.success(f"ราคาตลาด: **{current_thb_baht:,.0f}**")
else:
    st.sidebar.caption("กรอกราคาซื้อขายจริง")
    manual_price = st.sidebar.number_input("ราคาทอง (บาทละ)", value=40500, step=50)
    current_thb_baht = manual_price
    if df_gold is not None and 'RSI' in df_gold.columns: 
        current_rsi = df_gold['RSI'].iloc[-1]
        support_usd, resistance_usd = find_support_resistance(df_gold)

st.sidebar.markdown("---")
st.sidebar.header("📏 ตั้งค่า Grid")
gap_buy_1_2 = st.sidebar.number_input("ไม้ 1->2", value=500, step=100)
gap_buy_2_3 = st.sidebar.number_input("ไม้ 2->3", value=1000, step=100)
gap_3_4 = st.sidebar.number_input("ไม้ 3->4", value=800, step=50)
gap_4_5 = st.sidebar.number_input("ไม้ 4->5", value=1000, step=50)

st.sidebar.markdown("---")
gap_profit = st.sidebar.number_input("กำไรขั้นต่ำ/ไม้", value=300, step=50)
spread_buffer = st.sidebar.number_input("เผื่อ Spread", value=50.0, step=10.0)
base_trade_size = st.sidebar.number_input("เงินต้นเริ่มแรก", value=10000, step=1000)

# --- 6. AI Strategy Advisor ---
st.subheader("🧠 คำแนะนำกลยุทธ์ (AI Strategy)")

if df_gold is not None:
    last_close = df_gold['Close'].iloc[-1]
    ema200 = df_gold['EMA200'].iloc[-1]
    
    col_sniper, col_investor = st.columns(2)
    
    with col_sniper:
        st.markdown("#### ⚡ สายเก็งกำไร (Sniper)")
        sniper_msg, sniper_class = "", ""
        if current_rsi <= 30:
            sniper_msg, sniper_class = f"💎 **FIRE!**: RSI {current_rsi:.0f} ต่ำมาก (ซื้อสวน)", "buy-sig"
        elif current_rsi <= 45 and last_close > ema200:
            sniper_msg, sniper_class = f"🛒 **BUY DIP**: RSI {current_rsi:.0f} ย่อตัวสวย", "buy-sig"
        elif current_rsi >= 75:
            sniper_msg, sniper_class = f"💰 **SELL**: RSI {current_rsi:.0f} แพงแล้ว", "sell-sig"
        else:
            sniper_msg, sniper_class = f"⏳ **WAIT**: RSI {current_rsi:.0f} กลางๆ (ไม่ชัด)", "wait-sig"
        st.markdown(f'<div class="sig-box {sniper_class}">{sniper_msg}</div>', unsafe_allow_html=True)

    with col_investor:
        st.markdown("#### 🐢 สายออมยาว (Investor)")
        invest_msg, invest_class = "", ""
        if last_close > ema200:
            invest_msg, invest_class = "🐂 **HOLD**: ภาพใหญ่ขาขึ้น (Run Trend)", "hold-sig"
        else:
            invest_msg, invest_class = "🐻 **CAUTION**: หลุดแนวรับสำคัญ", "sell-sig"
        st.markdown(f'<div class="sig-box {invest_class}">{invest_msg}</div>', unsafe_allow_html=True)

# --- 7. Logic พอร์ต ---
portfolio = st.session_state.gold_data['portfolio']
last_active_wood = 0
last_entry_price = 0
for i in range(1, 6):
    if portfolio[str(i)]['status'] == 'ACTIVE':
        last_active_wood = i
        last_entry_price = portfolio[str(i)]['entry_price']

next_wood = last_active_wood + 1
trap_price = 0
trap_reason = ""

if next_wood == 1:
    trap_price = current_thb_baht - 100
    trap_reason = "ราคาตลาด / RSI เข้าเกณฑ์"
elif next_wood <= 5:
    gap = gap_buy_1_2 if next_wood == 2 else (gap_buy_2_3 if next_wood == 3 else (gap_3_4 if next_wood == 4 else gap_4_5))
    trap_price = last_entry_price - gap
    trap_reason = f"ระยะห่าง Grid {gap} บาท จากไม้ {last_active_wood}"

trap_price = round(trap_price / 50) * 50

# --- 8. Dashboard ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("โหมด", "Auto" if "Auto" in price_source else "Manual")
c2.metric("สถานะพอร์ต", f"{last_active_wood}/5 ไม้")
c3.metric("ราคาทองไทย", f"{current_thb_baht:,.0f} ฿")
current_capital = base_trade_size + st.session_state.gold_data.get('accumulated_profit', 0.0)
c4.metric("เงินทุน (ทบต้น)", f"{current_capital:,.0f} ฿")

if next_wood <= 5:
    st.info(f"📢 **ไม้ต่อไป ({next_wood}):** ตั้งรับที่ **{trap_price:,.0f}** บาท ({trap_reason})")
else:
    st.error("กระสุนหมด! หยุดซื้อและรอขาย")

st.write("---")

tab1, tab2, tab3 = st.tabs(["🔫 Sniper Board", "🧊 Vault", "📈 Technical Chart"])

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
                    if i == next_wood: st.markdown(f"📍 **รอช้อนที่:** `{trap_price:,.0f}`")
                else:
                    target_sell = wood['entry_price'] + gap_profit + spread_buffer
                    curr_profit = (current_thb_baht - spread_buffer - wood['entry_price']) * wood['grams']
                    color_pl = "green" if current_thb_baht >= target_sell else "red"
                    st.markdown(f"ทุน: **{wood['entry_price']:.0f}** | เป้า: **{target_sell:,.0f}**")
                    st.markdown(f"สถานะ: :{color_pl}[{curr_profit:+.0f} ฿]")

            with col_btn:
                if wood['status'] == 'EMPTY':
                    prev_active = True if i == 1 else portfolio[str(i-1)]['status'] == 'ACTIVE'
                    if prev_active:
                        if st.button(f"🔴 ยิงไม้ {i}", key=f"buy_{i}", use_container_width=True):
                            st.session_state.gold_data['portfolio'][key] = {
                                'status': 'ACTIVE', 'entry_price': current_thb_baht,
                                'grams': current_capital / current_thb_baht, 'date': datetime.now().strftime("%Y-%m-%d %H:%M")
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
        st.subheader("📈 กราฟทองคำ & RSI (1 Hour)")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3],
                            subplot_titles=("Price Action", "RSI Indicator"))

        fig.add_trace(go.Candlestick(x=df_gold.index, open=df_gold['Open'], high=df_gold['High'],
                        low=df_gold['Low'], close=df_gold['Close'], name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['EMA50'], name='EMA 50', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
        
        if price_source == "🤖 Auto (Spot)":
            fig.add_hline(y=support_usd, line_dash="dot", line_color="green", annotation_text="Support", row=1, col=1)
            fig.add_hline(y=resistance_usd, line_dash="dot", line_color="red", annotation_text="Resistance", row=1, col=1)

        fig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['RSI'], name='RSI', line=dict(color='purple', width=2)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
        fig.add_hrect(y0=30, y1=70, line_width=0, fillcolor="gray", opacity=0.1, row=2, col=1)

        fig.update_layout(height=600, xaxis_rangeslider_visible=False, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else: st.error("โหลดกราฟไม่ได้")

st.markdown("<div class='footer'>🛠️ Engineered by <b>โบ้ 50</b></div>", unsafe_allow_html=True)
