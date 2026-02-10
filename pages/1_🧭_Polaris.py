import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Zen V7.0", page_icon="💎", layout="wide")

# Custom CSS (Clean Look)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .status-box { padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 10px; }
    .buy-box { background-color: #dcfce7; color: #166534; border: 1px solid #166534; }
    .sell-box { background-color: #fee2e2; color: #991b1b; border: 1px solid #991b1b; }
    .wait-box { background-color: #f3f4f6; color: #374151; border: 1px solid #6b7280; }
    .hold-box { background-color: #e0f2fe; color: #1e40af; border: 1px solid #1e40af; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V7.0: Zen Edition (Fast & Stable)")
st.markdown("**ระบบเทรดฉบับลีน: ตัดความซับซ้อน เน้นความแม่นยำของกราฟและ RSI**")
st.write("---")

# --- 2. ฐานข้อมูลหุ้น (Static Data เพื่อความเร็ว) ---
# เราใส่ค่า DNA ไว้เลย ไม่ต้องเสียเวลาดึงจาก Yahoo ทุกครั้ง
STOCK_DB = {
    # หุ้นไทย
    "CPALL.BK": {"Type": "Growth", "Name": "CPALL"},
    "PTT.BK":   {"Type": "Dividend", "Name": "PTT"},
    "LH.BK":    {"Type": "Dividend", "Name": "LH"},
    "GULF.BK":  {"Type": "Growth", "Name": "GULF"},
    "SCB.BK":   {"Type": "Dividend", "Name": "SCB"},
    "ADVANC.BK":{"Type": "Dividend", "Name": "ADVANC"},
    "AOT.BK":   {"Type": "Growth", "Name": "AOT"},
    "KBANK.BK": {"Type": "Dividend", "Name": "KBANK"},
    "BDMS.BK":  {"Type": "Growth", "Name": "BDMS"},
    "PTTEP.BK": {"Type": "Dividend", "Name": "PTTEP"},
    "TISCO.BK": {"Type": "Dividend", "Name": "TISCO"},
    "CPAXT.BK": {"Type": "Growth", "Name": "CPAXT"},
    "CRC.BK":   {"Type": "Growth", "Name": "CRC"},
    "CPN.BK":   {"Type": "Growth", "Name": "CPN"},
    # กองทุน/นอก
    "SMH":      {"Type": "Growth", "Name": "SCBSEMI (SMH)"},
    "QQQ":      {"Type": "Growth", "Name": "SCBRMNDQ (QQQ)"},
    "SPY":      {"Type": "Growth", "Name": "SCBRMS&P500 (SPY)"},
    "QUAL":     {"Type": "Growth", "Name": "SCBGQUAL (QUAL)"},
    "GLD":      {"Type": "Asset", "Name": "Gold (GLD)"},
    "SLV":      {"Type": "Asset", "Name": "Silver (SLV)"},
    "AAPL":     {"Type": "Growth", "Name": "Apple"},
    "NVDA":     {"Type": "Growth", "Name": "Nvidia"}
}

ALL_TICKERS = list(STOCK_DB.keys())

# --- 3. ระบบดึงข้อมูล (Batch Processing) ---
@st.cache_data(ttl=3600)
def fetch_batch_data():
    try:
        # โหลดทีเดียวจบ เร็วและชัวร์
        data = yf.download(ALL_TICKERS, period="1y", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
        return data
    except: return None

def process_data(batch_data, ticker):
    try:
        if len(ALL_TICKERS) == 1: df = batch_data
        else: df = batch_data[ticker].copy()

        if df.empty or len(df) < 50: return None

        # คำนวณแค่นี้พอ (Core Indicators)
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except: return None

# --- 4. Dashboard ---
st.subheader("📊 Market Overview")

with st.spinner('กำลังสแกนตลาด...'):
    batch_data = fetch_batch_data()

if batch_data is not None:
    data_rows = []
    
    for ticker in ALL_TICKERS:
        df = process_data(batch_data, ticker)
        
        if df is not None:
            price = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            ema200 = df['EMA200'].iloc[-1]
            stock_info = STOCK_DB[ticker]
            
            # Logic ง่ายๆ แต่ทรงพลัง
            trend = "🐂 ขาขึ้น" if price > ema200 else "🐻 ขาลง"
            
            action = "Wait"
            status_color = "white"
            text_color = "black"

            if rsi <= 30:
                action = "🟢 BUY DIP"
                status_color = "#dcfce7"
            elif rsi >= 75:
                action = "🔴 TAKE PROFIT"
                status_color = "#fee2e2"
            elif 30 < rsi <= 45 and price > ema200:
                action = "🛒 ACCUMULATE"
                status_color = "#e0f2fe"
            
            data_rows.append({
                "Symbol": stock_info['Name'],
                "Ticker": ticker,
                "Price": price,
                "RSI": rsi,
                "Action": action,
                "Trend": trend,
                "Type": stock_info['Type'],
                "Color": status_color,
                "TextColor": text_color
            })

    # แสดงตาราง
    if data_rows:
        res_df = pd.DataFrame(data_rows)
        cols = ["Symbol", "Price", "RSI", "Action", "Trend", "Type"]
        
        def highlight_rows(row):
            return [f'background-color: {row["Color"]}; color: {row["TextColor"]}'] * len(row)

        st.dataframe(
            res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
            column_order=cols,
            height=400,
            use_container_width=True
        )

        # --- 5. เจาะลึก & แก้พอร์ต (Personal Doctor) ---
        st.write("---")
        col_chart, col_doc = st.columns([2, 1])
        
        with col_chart:
            st.subheader("🔍 Technical Chart")
            selected_name = st.selectbox("เลือกหุ้น:", res_df['Symbol'])
            selected_ticker = res_df[res_df['Symbol'] == selected_name]['Ticker'].values[0]
            
            df_chart = process_data(batch_data, selected_ticker)
            
            if df_chart is not None:
                # คำนวณแนวรับต้าน (20 วัน)
                low_20 = df_chart['Low'].tail(20).min()
                high_20 = df_chart['High'].tail(20).max()
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                
                # เส้นแนวรับต้าน
                fig.add_hline(y=low_20, line_dash="dot", line_color="green", row=1, col=1)
                fig.add_hline(y=high_20, line_dash="dot", line_color="red", row=1, col=1)
                
                # RSI
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI'], name='RSI', line=dict(color='purple')), row=2, col=1)
                fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
                fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
                
                fig.update_layout(height=500, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

        with col_doc:
            st.subheader("👨‍⚕️ Portfolio Doctor")
            st.info(f"กำลังวิเคราะห์: **{selected_name}**")
            
            stock_dna = STOCK_DNA[selected_ticker]['Type']
            curr_price = df_chart['Close'].iloc[-1]
            curr_rsi = df_chart['RSI'].iloc[-1]
            
            # Input
            avg_cost = st.number_input("ต้นทุนเฉลี่ย", value=0.0)
            qty = st.number_input("จำนวนหุ้น", value=0, step=100)
            
            if qty > 0 and avg_cost > 0:
                unrealized = (curr_price - avg_cost) * qty
                pct = (unrealized / (avg_cost * qty)) * 100
                
                # --- Logic การแพทย์ (Simple & Clean) ---
                if unrealized < 0:
                    st.error(f"📉 ติดดอย {pct:.2f}%")
                    
                    # ถัวเมื่อไหร่?
                    if curr_price <= low_20 * 1.01: # ราคาลงมาชนแนวรับ
                        if curr_rsi <= 40:
                            st.markdown(f'<div class="status-box buy-box">💉 ฉีดยา: ถัวได้! (ชนแนวรับ {low_20:.2f})</div>', unsafe_allow_html=True)
                            
                            # เครื่องคิดเลขถัว
                            add_money = st.number_input("เติมเงินถัว (บาท)", value=5000, step=1000)
                            if add_money > 0:
                                add_share = int(add_money / curr_price)
                                new_avg = ((avg_cost * qty) + add_money) / (qty + add_share)
                                st.write(f"👉 ทุนใหม่: **{new_avg:.2f}**")
                        else:
                            st.markdown(f'<div class="status-box wait-box">⏳ รอ RSI ต่ำกว่านี้อีกนิด</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-box wait-box">⏳ รอก่อน ยังไม่ถึงแนวรับ ({low_20:.2f})</div>', unsafe_allow_html=True)

                else:
                    st.success(f"🎉 กำไร {pct:.2f}%")
                    if stock_dna == "Dividend":
                        st.markdown(f'<div class="status-box hold-box">🛡️ หุ้นปันผล: ถือยาว (Let Profit Run)</div>', unsafe_allow_html=True)
                    else:
                        if curr_price >= high_20 * 0.99:
                            st.markdown(f'<div class="status-box sell-box">💰 หุ้นเติบโต: ชนต้านแล้ว ขายทำกำไร!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="status-box hold-box">🚀 ถือต่อ: ยังไม่ชนแนวต้าน ({high_20:.2f})</div>', unsafe_allow_html=True)
            else:
                st.caption("กรอกต้นทุนเพื่อรับใบสั่งยา")

else:
    st.error("ไม่สามารถเชื่อมต่อตลาดได้ กรุณากด Refresh (F5)")
