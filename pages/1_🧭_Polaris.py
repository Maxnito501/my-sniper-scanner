import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V5.8", page_icon="💎", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .buy-zone { background-color: #dcfce7; padding: 15px; border-radius: 10px; border: 2px solid #16a34a; text-align: center; }
    .wait-zone { background-color: #fff7ed; padding: 15px; border-radius: 10px; border: 2px solid #f97316; text-align: center; }
    .sell-zone { background-color: #fee2e2; padding: 15px; border-radius: 10px; border: 2px solid #dc2626; text-align: center; }
    .hold-zone { background-color: #f3f4f6; padding: 15px; border-radius: 10px; border: 2px solid #6b7280; text-align: center; }
    .personal-zone { background-color: #e0f2fe; padding: 15px; border-radius: 10px; border: 2px solid #0284c7; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V5.8: Stability Edition")
st.markdown("**ระบบเทรดครบวงจร: เน้นความเสถียรและป้องกันข้อมูลดีเลย์**")
st.write("---")

# --- 2. ข้อมูลหุ้นและกองทุน ---
STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", 
    "BDMS.BK", "PTTEP.BK",
    "TISCO.BK", "CPAXT.BK", "CRC.BK", "CPN.BK"
]

FUNDS = {
    "SCBSEMI (Semi-Conductor)": "SMH", 
    "SCBRMNDQ (Nasdaq-100)": "QQQ", 
    "SCBRMS&P500 (S&P 500)": "SPY", 
    "SCBGQUAL (Global Quality)": "QUAL", 
    "Gold (ทองคำโลก)": "GLD",
    "Silver (เงินโลก)": "SLV",      
    "Apple (King)": "AAPL",
    "Nvidia (AI God)": "NVDA"
}

# --- 3. ฟังก์ชันดึงข้อมูล (แยกส่วนเพื่อความชัวร์) ---
@st.cache_data(ttl=3600)
def get_data_from_yahoo(ticker):
    # 1. ดึงข้อมูลกราฟ (Technical) - อันนี้สำคัญสุด ห้ามพัง
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        # แก้ปัญหา MultiIndex (บั๊กยอดฮิต)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if len(df) < 50: return None, 0, 0, "-"

        # Indicators
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['VolMA'] = df['Volume'].rolling(20).mean()
    except:
        return None, 0, 0, "-"

    # 2. ดึงข้อมูลพื้นฐาน (Fundamental) - ถ้าพังให้ข้ามไป (ไม่ให้แอปค้าง)
    pe, div_yield, xd_date = 0, 0, "-"
    try:
        info = yf.Ticker(ticker).info
        pe = info.get('trailingPE', 0)
        raw_div = info.get('dividendYield', 0)
        div_yield = (raw_div * 100) if raw_div and raw_div < 1 else (raw_div if raw_div else 0)
        if div_yield > 20: div_yield = 0 # กรองค่า error
        
        xd_ts = info.get('exDividendDate')
        if xd_ts: xd_date = datetime.fromtimestamp(xd_ts).strftime('%d/%m/%Y')
    except:
        pass # ถ้าดึงงบไม่ได้ ช่างมัน เอาแค่กราฟพอ

    return df, pe, div_yield, xd_date

# --- 4. Strategy Engine ---
def analyze_data(df, pe, div):
    try:
        price = df['Close'].iloc[-1]
        ema200 = df['EMA200'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        if price > ema200:
            trend = "ขาขึ้น 🐂"
            strategy = "⭐ ถือยาว"
        else:
            trend = "ขาลง 🐻"
            strategy = "🛡️ เล่นสั้น/ถัว"
        
        action = "Wait"
        color = "white"
        text_color = "black"
        
        if rsi <= 35:
            action = "🟢 BUY MORE"
            color = "#dcfce7" # เขียวอ่อน
            text_color = "#166534"
        elif rsi >= 75:
            action = "🟠 PROFIT RUN"
            color = "#fef9c3" # เหลือง
            text_color = "#854d0e"
        elif 35 < rsi < 50 and price > ema200:
            action = "🛒 ACCUMULATE"
            color = "#dbeafe" # ฟ้าอ่อน
            text_color = "#1e40af"
            
        return price, rsi, trend, strategy, action, color, text_color
    except:
        return 0, 0, "-", "-", "-", "white", "black"

# --- 5. Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]

# Progress Bar
progress_text = "กำลังสแกนตลาด... กรุณารอสักครู่"
my_bar = st.progress(0, text=progress_text)

for i, (name, ticker) in enumerate(all_tickers):
    df, pe, div, xd = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, strat, act, col, txt_col = analyze_data(df, pe, div)
        
        data_list.append({
            "Symbol": name.replace(".BK", ""),
            "Ticker": ticker,
            "Price": price,
            "RSI": rsi,
            "Strategy": strat,
            "Action": act,
            "P/E": f"{pe:.1f}" if pe > 0 else "-",
            "Div %": f"{div:.2f}%" if div > 0 else "-",
            "XD Date": xd,
            "Trend": trend,
            "Color": col,
            "TextColor": txt_col
        })
    my_bar.progress((i + 1) / len(all_tickers), text=f"สแกน: {name}")

my_bar.empty()

if data_list:
    res_df = pd.DataFrame(data_list)
    cols = ["Symbol", "Price", "RSI", "Strategy", "Action", "P/E", "Div %", "XD Date"]
    
    # ฟังก์ชันระบายสีที่ปลอดภัย (แก้บั๊ก ValueError)
    def highlight_rows(row):
        bg_color = row['Color']
        txt_color = row['TextColor']
        return [f'background-color: {bg_color}; color: {txt_color}'] * len(row)

    # ใช้ subset เพื่อระบายสีเฉพาะคอลัมน์ที่โชว์
    st.dataframe(
        res_df.style.apply(highlight_rows, axis=1, subset=cols).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
        column_order=cols,
        height=500,
        use_container_width=True
    )

    # --- 6. Deep Dive ---
    st.write("---")
    
    col_chart, col_decision = st.columns([1.6, 1])
    
    with col_chart:
        st.subheader("🔍 Technical Chart")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้นเพื่อวิเคราะห์:", symbol_list)
        target = next((t for n, t in all_tickers if n.replace(".BK", "") == selected_symbol), None)

        if target:
            df_chart, _, div_yield, xd_date = get_data_from_yahoo(target)
            if df_chart is not None:
                current_price_default = float(df_chart['Close'].iloc[-1])
                recent_low = df_chart['Low'].tail(60).min()
                recent_high = df_chart['High'].tail(60).max()
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                
                fig.add_hline(y=recent_low, line_dash="dot", line_color="green", annotation_text="Support", row=1, col=1)
                fig.add_hline(y=recent_high, line_dash="dot", line_color="red", annotation_text="Resistance", row=1, col=1)
                
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

    with col_decision:
        st.subheader("🧠 Personal Advisor")
        st.markdown('<div class="personal-zone">', unsafe_allow_html=True)
        st.markdown(f"#### 💼 พอร์ต {selected_symbol}")
        
        avg_cost = st.number_input("ต้นทุนเฉลี่ย", value=0.0, step=0.1, format="%.2f", key=f"cost_{selected_symbol}")
        qty = st.number_input("จำนวนหุ้น", value=0, step=100, key=f"qty_{selected_symbol}")
        
        if target:
            rsi_val = df_chart['RSI'].iloc[-1]
            
            if qty > 0 and avg_cost > 0:
                market_val = current_price_default * qty
                cost_val = avg_cost * qty
                unrealized = market_val - cost_val
                pct = (unrealized / cost_val) * 100
                
                if unrealized < 0:
                    st.error(f"📉 ขาดทุน: {unrealized:,.0f} ฿ ({pct:.2f}%)")
                    if rsi_val <= 45:
                        st.markdown('<div class="buy-zone">🛒 <b>OPPORTUNITY:</b><br>ราคาย่อตัวลงมาสวย เหมาะแก่การซื้อถัว</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="hold-zone">🧱 <b>HOLD:</b><br>ราคายังไม่ถูกมาก รอไปก่อน</div>', unsafe_allow_html=True)
                else:
                    st.success(f"🎉 กำไร: +{unrealized:,.0f} ฿ (+{pct:.2f}%)")
                    st.markdown('<div class="hold-zone">💎 <b>LET PROFIT RUN:</b><br>ถือต่อไปครับ เทรนด์ยังดี</div>', unsafe_allow_html=True)
            else:
                st.info("กรอกข้อมูลเพื่อรับคำแนะนำ")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
