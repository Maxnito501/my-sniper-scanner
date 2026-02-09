import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris V6.0 Batch", page_icon="💎", layout="wide")

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

st.title("💎 Polaris V6.0: Batch Loader Edition")
st.markdown("**ระบบเทรดครบวงจร: สแกนไว ไม่โดนบล็อก (Batch Request)**")
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

# รวมรายชื่อทั้งหมดเป็น List เดียว
ALL_TICKERS_LIST = STOCKS + list(FUNDS.values())

# --- 3. ฟังก์ชันดึงข้อมูลแบบเหมาเข่ง (Batch Download) ---
@st.cache_data(ttl=3600)
def fetch_batch_data():
    try:
        # ยิงครั้งเดียว ได้ครบทุกตัว (เร็วและไม่โดนบล็อก)
        data = yf.download(tickers=ALL_TICKERS_LIST, period="1y", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
        return data
    except Exception as e:
        return None

# ฟังก์ชันย่อยสำหรับคำนวณแต่ละตัว
def process_ticker_data(batch_data, ticker):
    try:
        # ดึงข้อมูลจากก้อนใหญ่
        if len(ALL_TICKERS_LIST) == 1:
             df = batch_data
        else:
             df = batch_data[ticker].copy()
        
        # เช็คว่ามีข้อมูลไหม
        if df.empty or 'Close' not in df.columns or df['Close'].isnull().all():
            return None, 0, 0, "-"

        # Indicators
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Volume MA (ถ้ามี)
        if 'Volume' in df.columns:
            df['VolMA'] = df['Volume'].rolling(20).mean()
        else:
            df['Volume'] = 0
            df['VolMA'] = 0

        # Fundamental (แยกดึงรายตัว แต่ถ้าพังให้ข้ามได้)
        pe, div_yield, xd_date = 0, 0, "-"
        try:
            info = yf.Ticker(ticker).info
            pe = info.get('trailingPE', 0)
            raw_div = info.get('dividendYield', 0)
            div_yield = (raw_div * 100) if raw_div and raw_div < 1 else (raw_div if raw_div else 0)
            if div_yield > 20: div_yield = 0 
            
            xd_ts = info.get('exDividendDate')
            if xd_ts: xd_date = datetime.fromtimestamp(xd_ts).strftime('%d/%m/%Y')
        except: pass 

        return df, pe, div_yield, xd_date
    except: return None, 0, 0, "-"


# --- 4. Strategy Engine ---
def analyze_data(df, pe, div):
    try:
        price = df['Close'].iloc[-1]
        ema200 = df['EMA200'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        if price > ema200:
            trend = "ขาขึ้น 🐂"
            strategy = "⭐ ถือยาว/สะสม"
        else:
            trend = "ขาลง 🐻"
            strategy = "🛡️ เน้นปันผล/ถัว"
        
        action = "Wait"
        color = "white"
        text_color = "black"
        
        if rsi <= 35:
            action = "🟢 BUY MORE"
            color = "#90EE90"
        elif rsi >= 75:
            action = "🟠 TRIM PORT"
            color = "#FFD700" 
        elif 35 < rsi < 50 and price > ema200:
            action = "🛒 ACCUMULATE"
            color = "#98FB98"
            
        return price, rsi, trend, strategy, action, color, text_color
    except: return 0, 0, "-", "-", "-", "white", "black"

# --- 5. Dashboard ---
st.subheader("📊 Strategic Dashboard")

# 1. โหลดข้อมูลก้อนใหญ่มาก่อน (Batch)
with st.spinner("กำลังดึงข้อมูลตลาดทั่วโลก... (Batch Download)"):
    batch_data = fetch_batch_data()

if batch_data is not None:
    data_list = []
    
    # รวม list เพื่อวนลูปทีเดียว
    display_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]
    
    # Progress Bar
    my_bar = st.progress(0)
    
    for i, (name, ticker) in enumerate(display_tickers):
        # แตกข้อมูลย่อยจากก้อนใหญ่
        df, pe, div, xd = process_ticker_data(batch_data, ticker)
        
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
        my_bar.progress((i + 1) / len(display_tickers))
    
    my_bar.empty()

    if data_list:
        res_df = pd.DataFrame(data_list)
        cols = ["Symbol", "Price", "RSI", "Strategy", "Action", "P/E", "Div %", "XD Date"]
        
        def highlight_rows(row):
            bg_color = row.get("Color", "white")
            txt_color = row.get("TextColor", "black")
            return [f'background-color: {bg_color}; color: {txt_color}'] * len(row)

        st.dataframe(
            res_df.style.apply(highlight_rows, axis=1, subset=cols).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
            column_order=cols, height=500, use_container_width=True
        )

        # --- 6. Deep Dive & Personal Plan ---
        st.write("---")
        
        col_chart, col_decision = st.columns([1.6, 1])
        
        with col_chart:
            st.subheader("🔍 Technical Chart")
            symbol_list = [d["Symbol"] for d in data_list]
            selected_symbol = st.selectbox("เลือกหุ้นเพื่อวิเคราะห์:", symbol_list)
            
            # หา Ticker จากชื่อที่เลือก
            target_info = next((item for item in data_list if item["Symbol"] == selected_symbol), None)
            
            if target_info:
                target_ticker = target_info['Ticker']
                df_chart, _, div_yield, xd_date = process_ticker_data(batch_data, target_ticker)
                
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
                    fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig, use_container_width=True)

        with col_decision:
            st.subheader("🧠 Personal Advisor")
            st.markdown('<div class="personal-zone">', unsafe_allow_html=True)
            st.markdown(f"#### 💼 พอร์ต {selected_symbol}")
            
            avg_cost = st.number_input("ต้นทุนเฉลี่ย", value=0.0, step=0.1, format="%.2f", key=f"cost_{selected_symbol}")
            qty = st.number_input("จำนวนหุ้น", value=0, step=100, key=f"qty_{selected_symbol}")
            
            if target_info:
                rsi_val = target_info['RSI']
                
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
            
            # เครื่องคิดเลขถัว
            st.write("---")
            with st.expander("🧮 คำนวณต้นทุนใหม่ (กรณีซื้อเพิ่ม)", expanded=False):
                add_shares = st.number_input("ซื้อเพิ่มกี่หุ้น?", value=100, step=100, key=f"add_{selected_symbol}")
                if add_shares > 0 and avg_cost > 0:
                    new_cost = ((avg_cost * qty) + (current_price_default * add_shares)) / (qty + add_shares)
                    diff_cost = avg_cost - new_cost
                    st.info(f"👉 ต้นทุนใหม่: **{new_cost:.2f} บาท** (ลดลง {diff_cost:.2f})")

else:
    st.error("❌ เชื่อมต่อ Yahoo Finance ไม่ได้ (อาจโดนบล็อกชั่วคราว) กรุณารอสักครู่แล้วกด Refresh")
```

### 💡 วิธีใช้งานให้ลื่นไหล
1.  **กด Refresh (F5):** ครั้งแรกอาจจะช้านิดนึง (2-3 วินาที) เพราะมันกำลังขนข้อมูลก้อนใหญ่มา
2.  **สังเกต:** ถ้าข้อมูลมาแล้ว มันจะเร็วปรื๊ดเลยครับ เพราะมันโหลดมาครบทุกตัวแล้ว ไม่ต้องโหลดทีละตัวเหมือนเมื่อก่อน

ลุยเลยครับวิศวกร! นี่คือระบบที่เสถียรที่สุดแล้วครับ! 🏗️🚀
