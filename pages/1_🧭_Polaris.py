import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V6.0", page_icon="💎", layout="wide")

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
    .action-box { margin-top: 15px; padding: 10px; background-color: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V6.0: Batch Processing Edition")
st.markdown("**ระบบเทรดครบวงจร: สแกนไว ไม่โดนบล็อก (ใช้ระบบเหมาเข่ง)**")
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

ALL_TICKERS = STOCKS + list(FUNDS.values())

# --- 3. ฟังก์ชันดึงข้อมูลแบบเหมาเข่ง (Batch Fetch) ---
@st.cache_data(ttl=3600)
def fetch_batch_data():
    try:
        # โหลดข้อมูลทีเดียวทุกตัว (ลดการยิง Request ได้ 20 เท่า)
        data = yf.download(ALL_TICKERS, period="1y", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
        return data
    except: return None

def process_ticker_data(batch_data, ticker):
    try:
        # ดึงข้อมูลย่อยออกมาจากก้อนใหญ่
        if len(ALL_TICKERS) == 1:
            df = batch_data
        else:
            try:
                df = batch_data[ticker].copy()
            except KeyError:
                return None, 0, 0, "-"

        if df.empty or len(df) < 50: return None, 0, 0, "-"

        # Indicators
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        if 'Volume' in df.columns:
            df['VolMA'] = df['Volume'].rolling(20).mean()
        else:
            df['Volume'] = 0
            df['VolMA'] = 0

        # Fundamental (แยกดึง ถ้าพังให้ข้าม)
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

with st.spinner('กำลังดึงข้อมูลตลาดทั่วโลก... (Batch Download)'):
    batch_data = fetch_batch_data()

if batch_data is not None:
    data_list = []
    display_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]
    
    my_bar = st.progress(0)
    
    for i, (name, ticker) in enumerate(display_tickers):
        # แตกข้อมูลออกมาประมวลผลทีละตัว
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

        # --- 6. Deep Dive & Personal Advisor ---
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
                # ดึงข้อมูลกราฟเฉพาะตัวที่เลือกมาวาด
                df_chart, _, _, _ = process_ticker_data(batch_data, target_ticker)
                
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
            st.markdown(f"#### 💼 แผนการเล่น {selected_symbol}")
            
            avg_cost = st.number_input("ต้นทุนเฉลี่ย", value=0.0, step=0.1, format="%.2f", key=f"cost_{selected_symbol}")
            qty = st.number_input("จำนวนหุ้น", value=0, step=100, key=f"qty_{selected_symbol}")
            
            if target_info:
                rsi_val = target_info['RSI']
                
                # ... (Logic คำแนะนำส่วนตัว เหมือนเดิม) ...
                if qty > 0 and avg_cost > 0:
                    market_val = current_price_default * qty
                    cost_val = avg_cost * qty
                    unrealized = market_val - cost_val
                    pct = (unrealized / cost_val) * 100
                    
                    if unrealized < 0:
                        st.error(f"📉 ขาดทุน: {unrealized:,.0f} ฿ ({pct:.2f}%)")
                        if current_price_default <= recent_low * 1.01:
                             if rsi_val <= 45:
                                 st.markdown('<div class="buy-zone"><h3>✅ ซื้อถัวได้!</h3><p>ราคาชนแนวรับ + RSI ต่ำ</p></div>', unsafe_allow_html=True)
                             else:
                                 st.markdown('<div class="wait-zone"><h3>🤔 รอก่อน</h3><p>ชนรับแล้ว แต่ RSI ยังสูง</p></div>', unsafe_allow_html=True)
                        else:
                             st.markdown('<div class="hold-zone"><h3>⏳ ถือรอ</h3><p>ราคายังลอยอยู่กลางทาง</p></div>', unsafe_allow_html=True)
                    else:
                        st.success(f"🎉 กำไร: +{unrealized:,.0f} ฿ (+{pct:.2f}%)")
                        if current_price_default >= recent_high * 0.99:
                            st.markdown('<div class="sell-zone"><h3>💰 พิจารณาขาย</h3><p>ชนต้านเดิม</p></div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="hold-zone"><h3>💎 รันเทรนด์</h3><p>ถือลุ้น High เดิม</p></div>', unsafe_allow_html=True)
                
                # ส่วนแนะนำคนไม่มีของ
                st.write("")
                st.markdown('<div class="action-box">', unsafe_allow_html=True)
                st.markdown(f"#### 🛒 แผนสำหรับเงินก้อนใหม่")
                
                buy_status, buy_color = "", ""
                if current_price_default <= recent_low * 1.015:
                    if rsi_val <= 45: buy_status, buy_color = "✅ **BUY NOW:** ราคาสวย!", "green"
                    else: buy_status, buy_color = "🤔 **WAIT:** RSI ยังสูง", "orange"
                elif current_price_default >= recent_high * 0.985:
                    buy_status, buy_color = "⛔ **DON'T BUY:** ชนเพดาน", "red"
                else:
                    buy_status, buy_color = f"⏳ **WAIT:** รอที่ {recent_low:.2f}", "gray"
                     
                st.markdown(f":{buy_color}[{buy_status}]")
                st.caption(f"ราคา: {current_price_default:.2f} | รับ: {recent_low:.2f} | ต้าน: {recent_high:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                with st.expander("🧮 คำนวณต้นทุนใหม่", expanded=False):
                    add_shares = st.number_input("ซื้อเพิ่มกี่หุ้น?", value=100, step=100, key=f"add_{selected_symbol}")
                    if add_shares > 0 and avg_cost > 0:
                        new_cost = ((avg_cost * qty) + (current_price_default * add_shares)) / (qty + add_shares)
                        diff_cost = avg_cost - new_cost
                        st.info(f"👉 ต้นทุนใหม่: **{new_cost:.2f} บาท** (ลดลง {diff_cost:.2f})")

            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.error("ไม่พบข้อมูลหุ้น")

else:
    st.error("⚠️ ไม่สามารถดึงข้อมูลตลาดได้ (กรุณากด Refresh)")
