import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import os

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Momentum Sniper (High Risk)", page_icon="🚀", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .bull-box { background-color: #dcfce7; padding: 15px; border-radius: 10px; border: 2px solid #16a34a; text-align: center; }
    .bear-box { background-color: #fee2e2; padding: 15px; border-radius: 10px; border: 2px solid #dc2626; text-align: center; }
    .target-box { background-color: #f0f9ff; padding: 15px; border-radius: 10px; border: 2px solid #0ea5e9; text-align: center; }
    
    .big-num { font-size: 1.5rem; font-weight: bold; }
    .profit-text { color: #166534; font-weight: bold; }
    .loss-text { color: #991b1b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Momentum Sniper: Hit & Run Strategy")
st.markdown("**ระบบเทรดหุ้นซิ่ง: เน้นรอบจัด กำไร 10% / คัท 5% (ห้ามถือยาว!)**")
st.write("---")

# --- 2. รายชื่อหุ้นสายซิ่ง (พร้อมชื่อไทย) ---
RACING_STOCKS_INFO = {
    "DELTA.BK": "Delta Electronics (ชิ้นส่วนอิเล็กฯ)",
    "HANA.BK": "Hana Microelectronics (ชิ้นส่วนอิเล็กฯ)",
    "KCE.BK": "KCE Electronics (แผ่นพิมพ์วงจร)",
    "JMT.BK": "JMT Network (บริหารหนี้เสีย)",
    "JMART.BK": "Jaymart Group (โฮลดิ้ง/มือถือ)",
    "SINGER.BK": "Singer Thailand (เช่าซื้อ)",
    "GULF.BK": "Gulf Energy (โรงไฟฟ้า)",
    "EA.BK": "Energy Absolute (พลังงานหมุนเวียน)",
    "GPSC.BK": "Global Power Synergy (โรงไฟฟ้า PTT)",
    "SCBSEMI": "SCB Semiconductor (กองทุนชิป)"
}
RACING_STOCKS = list(RACING_STOCKS_INFO.keys())
FUNDS_MAP = {"SCBSEMI": "SMH"}

# --- 3. ฟังก์ชันแจ้งเตือน (ยกเครื่องมาใส่) ---
def send_notify(message):
    # LINE
    if 'LINE_ACCESS_TOKEN' in st.secrets and 'LINE_USER_ID' in st.secrets:
        try:
            url = 'https://api.line.me/v2/bot/message/push'
            headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {st.secrets['LINE_ACCESS_TOKEN']}"}
            data = {'to': st.secrets['LINE_USER_ID'], 'messages': [{'type': 'text', 'text': message.replace('*', '')}]}
            requests.post(url, headers=headers, json=data)
        except: pass

    # Telegram
    if 'telegram_token' in st.secrets and 'telegram_chat_id' in st.secrets:
        try:
            url = f"https://api.telegram.org/bot{st.secrets['telegram_token']}/sendMessage"
            requests.post(url, json={"chat_id": st.secrets['telegram_chat_id'], "text": message, "parse_mode": "Markdown"})
        except: pass

# --- 4. ฟังก์ชันคำนวณ (Momentum Indicators) ---
@st.cache_data(ttl=300)
def get_momentum_data(ticker):
    try:
        symbol = FUNDS_MAP.get(ticker, ticker)
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # Indicators
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        return df
    except: return None

def analyze_momentum(df):
    price = df['Close'].iloc[-1]
    ema10 = df['EMA10'].iloc[-1]
    ema50 = df['EMA50'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    macd = df['MACD'].iloc[-1]
    signal = df['Signal'].iloc[-1]
    
    status = "Wait"
    color = "white"
    
    # Logic ซิ่ง: ราคาเหนือ EMA10 + MACD ตัดขึ้น + RSI มีแรง (50-75)
    if price > ema10 and macd > signal and rsi > 50:
        if rsi < 75:
            status = "🚀 LUI (ลุย!)"
            color = "#dcfce7"
        else:
            status = "🔥 HOT (ระวัง)"
            color = "#fef9c3"
    elif price < ema10:
        status = "💤 SLEEP"
        color = "#f3f4f6"
    
    return price, rsi, macd, status, color

# --- 5. Dashboard ---

# Sidebar: ปุ่มแจ้งเตือน
st.sidebar.title("🏎️ Sniper Control")
if st.sidebar.button("🚀 สแกน & ส่งเข้ามือถือ"):
    with st.spinner("กำลังเร่งเครื่องสแกน..."):
        msg = ""
        for ticker in RACING_STOCKS:
            df = get_momentum_data(ticker)
            if df is not None:
                p, r, m, s, c = analyze_momentum(df)
                if "LUI" in s:
                    name = RACING_STOCKS_INFO.get(ticker, ticker)
                    msg += f"\n🏎️ *{name}*\nราคา: {p:.2f} | RSI: {r:.1f} | 🚀 ลุยได้!\n"
        
        if msg:
            full_msg = f"🚀 **MOMENTUM ALERT** 🚀\nหุ้นซิ่งเข้าสูตร:{msg}"
            send_notify(full_msg)
            st.sidebar.success("ส่งสัญญาณเข้ามือถือแล้ว! ✅")
        else:
            st.sidebar.info("ตลาดเงียบ ยังไม่มีตัวไหนน่าซิ่ง")


col_list, col_calc = st.columns([2, 1])

with col_list:
    st.subheader("🏎️ สนามประลองความเร็ว (Scanner)")
    
    data_list = []
    my_bar = st.progress(0)
    
    for i, ticker in enumerate(RACING_STOCKS):
        df = get_momentum_data(ticker)
        if df is not None:
            price, rsi, macd, status, col = analyze_momentum(df)
            name_th = RACING_STOCKS_INFO.get(ticker, ticker) # ดึงชื่อไทย
            
            data_list.append({
                "Symbol": ticker.replace(".BK", ""),
                "Name": name_th,
                "Price": price,
                "RSI": rsi,
                "MACD": macd,
                "Signal": status,
                "Color": col
            })
        my_bar.progress((i + 1) / len(RACING_STOCKS))
    
    my_bar.empty()
    
    if data_list:
        res_df = pd.DataFrame(data_list)
        
        def highlight_rows(row):
            return [f'background-color: {row["Color"]}; color: black'] * len(row)

        st.dataframe(
            res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}", "MACD": "{:.2f}"}),
            column_order=["Symbol", "Name", "Price", "Signal", "RSI", "MACD"], # เพิ่มคอลัมน์ Name
            height=500,
            use_container_width=True
        )

# --- 6. เครื่องคิดเลข 10/5 ---
with col_calc:
    st.subheader("🧮 แผนเทรด (Trade Setup)")
    
    with st.container(border=True):
        st.info("💡 **กฎเหล็กวิศวกร:** เข้าเร็ว ออกไว ห้ามใจอ่อน")
        
        stock_select = st.selectbox("เลือกหุ้นที่จะเล่น:", [d['Symbol'] for d in data_list] if data_list else [])
        
        current_p = 0.0
        if data_list:
            current_p = next((item['Price'] for item in data_list if item["Symbol"] == stock_select), 0.0)
        
        entry_price = st.number_input("ราคาเข้าซื้อ (บาท)", value=current_p, step=0.25)
        budget = st.number_input("เงินหน้าตัก (บาท)", value=10000, step=1000)
        
        if entry_price > 0:
            qty = int(budget / entry_price)
            take_profit = entry_price * 1.10
            stop_loss = entry_price * 0.95
            profit_amt = (take_profit - entry_price) * qty
            loss_amt = (entry_price - stop_loss) * qty
            
            st.write("---")
            st.markdown(f"""
            <div class="target-box"><div>จำนวนที่ซื้อได้: <b>{qty:,} หุ้น</b></div></div><br>
            <div class="bull-box"><div>🎯 <b>เป้าขาย: {take_profit:.2f}</b></div><div class="profit-text">+10% (กำไร {profit_amt:,.0f} บาท)</div></div><br>
            <div class="bear-box"><div>🛑 <b>จุดหนี: {stop_loss:.2f}</b></div><div class="loss-text">-5% (ขาดทุน {loss_amt:,.0f} บาท)</div><small>*หลุดราคานี้ต้องโยนซ้ายทันที*</small></div>
            """, unsafe_allow_html=True)

# --- 7. กราฟเทคนิค ---
st.write("---")
st.subheader(f"📈 กราฟความเร็วสูง: {stock_select}")

if stock_select:
    ticker_chart = next((t for t in RACING_STOCKS if t.replace(".BK", "") == stock_select), None)
    df_chart = get_momentum_data(ticker_chart)
    
    if df_chart is not None:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA10'], name='EMA 10 (Fast)', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA50'], name='EMA 50 (Trend)', line=dict(color='blue', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD'], name='MACD', line=dict(color='green')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Signal'], name='Signal', line=dict(color='red', dash='dot')), row=2, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="gray", row=2, col=1)
        fig.update_layout(height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
