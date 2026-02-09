import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V6.2 Fixed", page_icon="💎", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .sniper-card { background-color: #fff1f2; padding: 15px; border-radius: 10px; border: 2px solid #e11d48; margin-bottom: 15px; }
    .doctor-card { background-color: #eff6ff; padding: 15px; border-radius: 10px; border: 2px solid #3b82f6; margin-bottom: 15px; }
    
    .buy-text { color: #166534; font-weight: bold; font-size: 1.1em; }
    .sell-text { color: #991b1b; font-weight: bold; font-size: 1.1em; }
    .wait-text { color: #854d0e; font-weight: bold; font-size: 1.1em; }
    
    .metric-value { font-size: 1.2rem; font-weight: bold; }
    .metric-label { font-size: 0.9rem; color: #6b7280; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V6.2: Sniper & Doctor (Bug Fixed)")
st.markdown("**วิเคราะห์แยก 2 มุมมอง: เก็งกำไรระยะสั้น (Sniper) และ แก้พอร์ตระยะยาว (Doctor)**")
st.write("---")

# --- 2. ข้อมูลหุ้นและนิสัย (Stock DNA) ---
STOCK_DNA = {
    # สายปันผล
    "PTT.BK": "Dividend", "LH.BK": "Dividend", "TISCO.BK": "Dividend", 
    "SCB.BK": "Dividend", "KBANK.BK": "Dividend", "ADVANC.BK": "Dividend",
    "PTTEP.BK": "Dividend", 
    # สายเติบโต
    "CPALL.BK": "Growth", "GULF.BK": "Growth", "AOT.BK": "Growth", 
    "BDMS.BK": "Growth", "CPAXT.BK": "Growth", "CRC.BK": "Growth", "CPN.BK": "Growth",
    # กองทุน
    "SMH": "Growth", "QQQ": "Growth", "SPY": "Growth", "QUAL": "Growth", 
    "GLD": "Asset", "SLV": "Asset", "AAPL": "Growth", "NVDA": "Growth"
}

STOCKS = [k for k in STOCK_DNA.keys() if ".BK" in k]
FUNDS = {k: k for k in STOCK_DNA.keys() if ".BK" not in k}

# --- 3. ฟังก์ชันดึงข้อมูล ---
@st.cache_data(ttl=3600)
def get_data_from_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if len(df) < 50: return None, 0, 0, "-"

        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['VolMA'] = df['Volume'].rolling(20).mean()

        pe = stock.info.get('trailingPE', 0)
        raw_div = stock.info.get('dividendYield', 0)
        div_yield = (raw_div * 100) if raw_div and raw_div < 1 else (raw_div if raw_div else 0)
        if div_yield > 20: div_yield = 0
        
        xd_ts = stock.info.get('exDividendDate')
        xd_date = datetime.fromtimestamp(xd_ts).strftime('%d/%m/%Y') if xd_ts else "-"

        return df, pe, div_yield, xd_date
    except: return None, 0, 0, "-"

# --- 4. Strategy Engine ---
def analyze_data(df, pe, div):
    price = df['Close'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    trend = "ขาขึ้น 🐂" if price > ema200 else "ขาลง 🐻"
    
    action = "Wait"
    color = "white"
    text_color = "black"
    
    if rsi <= 35:
        action = "🟢 BUY (ถูก)"
        color = "#dcfce7"
        text_color = "#166534"
    elif rsi >= 75:
        action = "🔴 SELL (แพง)"
        color = "#fee2e2"
        text_color = "#991b1b"
    elif 35 < rsi < 50 and price > ema200:
        action = "🛒 ACCUMULATE"
        color = "#dbeafe"
        text_color = "#1e40af"
        
    return price, rsi, trend, action, color, text_color

# --- 5. Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]

my_bar = st.progress(0)

for i, (name, ticker) in enumerate(all_tickers):
    df, pe, div, xd = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, act, col, txt_col = analyze_data(df, pe, div)
        name_show = name.replace(".BK", "")
        
        data_list.append({
            "Symbol": name_show, "Ticker": ticker, "Price": price, "RSI": rsi,
            "Action": act, "P/E": f"{pe:.1f}" if pe else "-",
            "Div %": f"{div:.2f}%" if div else "-", "XD Date": xd,
            "Trend": trend, "Color": col, "TextColor": txt_col
        })
    my_bar.progress((i + 1) / len(all_tickers))
my_bar.empty()

if data_list:
    res_df = pd.DataFrame(data_list)
    cols = ["Symbol", "Price", "RSI", "Action", "P/E", "Div %", "Trend", "XD Date"]
    
    # 🛠️ FIX: ฟังก์ชันระบายสีที่ถูกต้อง (ไม่ใช้ subset ใน apply)
    def highlight_rows(row):
        bg_color = row.get("Color", "white")
        txt_color = row.get("TextColor", "black")
        return [f'background-color: {bg_color}; color: {txt_color}'] * len(row)

    # 🛠️ FIX: ลบ subset=cols ออกจาก apply เพื่อให้เห็นคอลัมน์ Color
    styler = res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}"})

    st.dataframe(
        styler,
        column_order=cols, # เลือกโชว์เฉพาะคอลัมน์ที่ต้องการตรงนี้
        height=400, 
        use_container_width=True
    )

    # --- 6. Deep Dive & Dual Advisor ---
    st.write("---")
    col_chart, col_advice = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("🔍 Technical Chart")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้นเพื่อวิเคราะห์:", symbol_list)
        target = next((item for item in data_list if item["Symbol"] == selected_symbol), None)

        if target:
            ticker = target['Ticker']
            df_chart, _, div_yield, xd_date = get_data_from_yahoo(ticker)
            
            if df_chart is not None:
                curr_price = float(df_chart['Close'].iloc[-1])
                recent_low = df_chart['Low'].tail(20).min()
                recent_high = df_chart['High'].tail(20).max()
                ema_50 = df_chart['EMA50'].iloc[-1]
                
                support_level = max(recent_low, ema_50) if curr_price > ema_50 else recent_low
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA50'], name='EMA 50', line=dict(color='orange', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                
                fig.add_hline(y=support_level, line_dash="dot", line_color="green", annotation_text="Support", row=1, col=1)
                fig.add_hline(y=recent_high, line_dash="dot", line_color="red", annotation_text="Resistance", row=1, col=1)
                
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

    with col_advice:
        st.subheader("💡 Strategic Advisor")
        
        if target:
            rsi_val = df_chart['RSI'].iloc[-1]
            stock_type = STOCK_DNA.get(ticker, "Growth")
            
            # Sniper Mode
            st.markdown('<div class="sniper-card">', unsafe_allow_html=True)
            st.markdown("#### 🔫 Sniper Mode (เล่นสั้น)")
            
            sniper_status = ""
            if curr_price >= recent_high * 0.99:
                sniper_status = f"<span class='sell-text'>💰 TAKE PROFIT:</span> ราคาชนต้าน ({recent_high:.2f}) ขายทำรอบ!"
            elif rsi_val <= 45 and curr_price <= support_level * 1.015:
                sniper_status = f"<span class='buy-text'>🚀 FIRE NOW:</span> ชนแนวรับ ({support_level:.2f}) + RSI ต่ำ ({rsi_val:.0f})"
            elif rsi_val <= 30:
                sniper_status = f"<span class='buy-text'>💎 PANIC BUY:</span> ของถูกมาก (RSI {rsi_val:.0f}) สวนเทรนด์ได้"
            else:
                sniper_status = f"<span class='wait-text'>⏳ WAIT:</span> ราคากลางๆ รอรับที่ {support_level:.2f}"
                
            st.markdown(sniper_status, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Doctor Mode
            st.markdown('<div class="doctor-card">', unsafe_allow_html=True)
            st.markdown(f"#### 👨‍⚕️ Doctor Mode (แก้พอร์ต {stock_type})")
            
            c1, c2 = st.columns(2)
            avg_cost = c1.number_input("ทุนเฉลี่ย", value=0.0, step=0.1, key=f"c_{selected_symbol}")
            qty = c2.number_input("จำนวนหุ้น", value=0, step=100, key=f"q_{selected_symbol}")
            
            if qty > 0 and avg_cost > 0:
                unrealized = (curr_price - avg_cost) * qty
                pct = (unrealized / (avg_cost * qty)) * 100
                
                if unrealized < 0:
                    st.error(f"📉 ติดดอย {unrealized:,.0f} ({pct:.2f}%)")
                    if curr_price <= support_level * 1.015:
                         st.info(f"💉 **แนะนำ:** ซื้อถัวได้! (ราคาถึงแนวรับแล้ว)")
                    else:
                         st.warning(f"✋ **แนะนำ:** อย่าเพิ่งถัว (รอก่อน) รอที่ {support_level:.2f}")
                else:
                    st.success(f"🎉 กำไร {unrealized:,.0f} ({pct:.2f}%)")
                    if stock_type == "Dividend":
                        st.info(f"🛡️ **แนะนำ:** ถือยาวกินปันผล ({div_yield:.2f}%)")
                    else:
                        st.info(f"💎 **แนะนำ:** รันเทรนด์ต่อ")
            else:
                st.caption("กรอกต้นทุนเพื่อรับคำแนะนำการแก้พอร์ต")
                
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
