import streamlit as st
import yfinance as yf
import pandas as pd
import warnings

# 1. สั่งปิด Warning สีแดงๆ ที่น่ารำคาญ
warnings.filterwarnings("ignore")

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Sniper Stock Scanner", layout="wide", page_icon="🔫")

DEFAULT_STOCKS = ["CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"]

st.sidebar.title("🔫 Sniper Control")
selected_stocks = st.sidebar.multiselect("เลือกหุ้นที่ต้องการเล็ง:", DEFAULT_STOCKS, default=DEFAULT_STOCKS)
rsi_period = st.sidebar.slider("RSI Period", 7, 30, 14)
rsi_lower = st.sidebar.number_input("จุดยิง (RSI Buy Zone)", value=30)
rsi_upper = st.sidebar.number_input("จุดขาย (RSI Sell Zone)", value=70)

st.title("🔫 Sniper Stock Scanner: กราฟเส้น (Clean Ver.)")
st.markdown("**(ข้อมูล Delay ประมาณ 15 นาที)**")

# ฟังก์ชันคำนวณ RSI
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stock_data(ticker):
    try:
        # auto_adjust=True ช่วยให้ข้อมูลราคาถูกต้องขึ้น
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if len(df) == 0: return None
        
        # แก้ปัญหา Column ซ้อน (MultiIndex) ที่ทำให้เกิด Warning
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # คำนวณ RSI
        df['RSI'] = calculate_rsi(df['Close'], period=rsi_period)
        return df
    except: return None

# ส่วนแสดงผล
scan_results = []
for symbol in selected_stocks:
    df = get_stock_data(symbol)
    if df is not None:
        # ดึงราคาแบบใหม่ (ใช้ .iloc[-1].item() เพื่อไม่ให้เกิด Warning)
        try:
            last_price = float(df['Close'].iloc[-1].item()) if hasattr(df['Close'].iloc[-1], 'item') else float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2].item()) if hasattr(df['Close'].iloc[-2], 'item') else float(df['Close'].iloc[-2])
            last_rsi = float(df['RSI'].iloc[-1].item()) if hasattr(df['RSI'].iloc[-1], 'item') else float(df['RSI'].iloc[-1])
        except:
            # Fallback ถ้าดึงไม่ได้จริงๆ
            last_price = float(df['Close'].values[-1])
            prev_price = float(df['Close'].values[-2])
            last_rsi = float(df['RSI'].values[-1])

        change_pct = ((last_price - prev_price) / prev_price) * 100
        
        signal = "WAIT ✋"
        color = "gray"
        if last_rsi <= rsi_lower:
            signal = "FIRE! (BUY) 🔫"
            color = "green"
        elif last_rsi >= rsi_upper:
            signal = "TAKE PROFIT 💰"
            color = "red"
        elif last_rsi <= rsi_lower + 5:
            signal = "PREPARE ⚠️"
            color = "orange"
            
        scan_results.append({"Symbol": symbol, "Price": last_price, "Change %": change_pct, "RSI": last_rsi, "Signal": signal, "Color": color})

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📡 เรดาร์จับสัญญาณ")
    for res in scan_results:
        with st.container(border=True):
            st.markdown(f"### {res['Symbol'].replace('.BK', '')}")
            st.markdown(f"ราคา: **{res['Price']:.2f}** ({res['Change %']:.2f}%)")
            st.markdown(f"RSI: **{res['RSI']:.2f}**")
            if res['Color'] == 'green': st.success(res['Signal'])
            elif res['Color'] == 'red': st.error(res['Signal'])
            elif res['Color'] == 'orange': st.warning(res['Signal'])
            else: st.info(res['Signal'])

with col2:
    st.subheader("📈 กราฟแนวโน้ม")
    chart_symbol = st.selectbox("เลือกดูตัวไหนดี:", selected_stocks)
    
    df_chart = get_stock_data(chart_symbol)
    
    if df_chart is not None:
        st.line_chart(df_chart['Close'], color="#00FF00")
        
        current_rsi = df_chart['RSI'].iloc[-1]
        # แปลงเป็น float ให้ชัวร์ก่อนแสดงผล
        val_rsi = float(current_rsi.item()) if hasattr(current_rsi, 'item') else float(current_rsi)
        
        st.metric("RSI ปัจจุบัน", f"{val_rsi:.2f}")
        st.progress(min(val_rsi / 100, 1.0))
        st.caption("แถบความร้อน RSI: ซ้าย (0) = ถูกมาก | ขวา (100) = แพงมาก")
    else:
        st.error("โหลดข้อมูลกราฟไม่ได้ ลองกดเลือกหุ้นตัวอื่นดูครับ")
