import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Suchat50 Dashboard", page_icon="📈")
st.title("📈 Suchat50: Stock Sniper Monitor")
st.write("ระบบติดตามหุ้นและกองทุนฉบับวิศวกร (RSI Strategy)")

# --- 2. รายชื่อหุ้น (Watchlist) ---
tickers = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", 
    "BDMS.BK", "PTTEP.BK"
]

# อัปเดตรายชื่อกองทุน (เพิ่ม SCBGQUAL)
funds = {
    "SCBSEMI (Semi-Conductor)": "SMH", 
    "SCBRMNDQ (Nasdaq-100)": "QQQ", 
    "SCBRMS&P500 (S&P 500)": "SPY", 
    "SCBGQUAL (Global Quality)": "QUAL", # <--- น้องใหม่สายคุณภาพ
    "Gold (ทองคำโลก)": "GLD"
}

# --- 3. ส่วนควบคุมด้านข้าง ---
st.sidebar.header("เมนูเลือกหุ้น")
selected_stock = st.sidebar.selectbox("เลือกหุ้นไทย", tickers)
selected_fund = st.sidebar.selectbox("เลือกกองทุน/สินทรัพย์", list(funds.keys()))

# --- 4. ฟังก์ชันคำนวณ RSI ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 5. ฟังก์ชันแสดงกราฟ ---
def plot_chart(ticker, name):
    st.subheader(f"กราฟราคา: {name}")
    
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if len(df) > 0:
            df['RSI'] = calculate_rsi(df['Close'])
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='Price'))
            
            st.plotly_chart(fig, use_container_width=True)
            
            last_rsi = df['RSI'].iloc[-1]
            st.metric("RSI ปัจจุบัน", f"{last_rsi:.2f}")
            
            if last_rsi <= 30:
                st.error(f"🔥 RSI ต่ำกว่า 30 ({last_rsi:.2f}) - น่าสนใจเข้าซื้อ!")
            elif last_rsi >= 70:
                st.warning(f"⚠️ RSI สูงเกินไป ({last_rsi:.2f}) - ระวังดอย!")
            else:
                st.info("สถานการณ์ปกติ")
                
        else:
            st.error("ไม่สามารถดึงข้อมูลได้")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")

# --- 6. แสดงผล ---
tab1, tab2 = st.tabs(["🇹🇭 หุ้นไทย", "🌎 กองทุนโลก"])

with tab1:
    plot_chart(selected_stock, selected_stock)

with tab2:
    ticker_symbol = funds[selected_fund]
    plot_chart(ticker_symbol, selected_fund)

st.write("---")
st.caption("Created by Suchat50 System | Data by Yahoo Finance")