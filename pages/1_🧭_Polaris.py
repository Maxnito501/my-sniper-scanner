import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V5.6", page_icon="💎", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .sniper-zone { background-color: #fee2e2; padding: 15px; border-radius: 10px; border: 2px dashed #ef4444; text-align: center; }
    .investor-zone { background-color: #dcfce7; padding: 15px; border-radius: 10px; border: 2px dashed #22c55e; text-align: center; }
    .personal-zone { background-color: #e0f2fe; padding: 15px; border-radius: 10px; border: 2px solid #0284c7; }
    .buy-box { background-color: #f0fdf4; padding: 10px; border-radius: 5px; border-left: 5px solid #16a34a; margin-top: 10px; }
    .wait-box { background-color: #fef2f2; padding: 10px; border-radius: 5px; border-left: 5px solid #dc2626; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V5.6: Personal Portfolio Advisor")
st.markdown("**ระบบเทรดครบวงจร: สแกนหุ้น -> วิเคราะห์กราฟ -> วางแผนแก้พอร์ตส่วนตัว**")
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

# --- 3. ฟังก์ชันดึงข้อมูล (Core Engine) ---
@st.cache_data(ttl=3600)
def get_data_from_yahoo(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        if len(df) < 100: return None, 0, 0

        # Indicators
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        df['VolMA'] = df['Volume'].rolling(20).mean()

        # Fundamental
        pe, div_yield = 0, 0
        try:
            info = yf.Ticker(ticker).info
            pe = info.get('trailingPE', 0)
            raw_div = info.get('dividendYield', 0)
            if raw_div is not None:
                temp_div = raw_div * 100 if raw_div < 1 else raw_div
                div_yield = 0 if temp_div > 20 else temp_div
        except: pass

        return df, pe, div_yield
    except: return None, 0, 0

@st.cache_data(ttl=300) 
def get_news_sentiment(ticker):
    try:
        news = yf.Ticker(ticker).news
        return [], "⚪ Neutral", 0
    except: return [], "⚪ Neutral", 0

# --- 4. Strategy Engine ---
def analyze_data(df, pe, div):
    price = df['Close'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    vol_ma = df['VolMA'].iloc[-1]
    
    if price > ema200:
        trend = "ขาขึ้น 🐂"
        strategy = "⭐ ถือยาว"
    else:
        trend = "ขาลง 🐻"
        strategy = "⚡ เล่นสั้น"
    
    action = "Wait"
    color = "white"
    text_color = "black"
    
    if rsi <= 30:
        action = "🟢 BUY DIP"
        color = "#90EE90"
    elif rsi >= 70:
        action = "🔴 SELL"
        color = "#FFB6C1"
    elif 30 < rsi < 45 and price > ema200:
        action = "➕ BUY MORE"
        color = "#98FB98"
    
    vol_status = "🔥 Vol พีค!" if vol > vol_ma * 1.5 else ""
    
    return price, rsi, trend, strategy, action, color, text_color, vol_status

# --- 5. Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]
my_bar = st.progress(0)

for i, (name, ticker) in enumerate(all_tickers):
    df, pe, div = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, strat, act, col, txt_col, vol_st = analyze_data(df, pe, div)
        
        data_list.append({
            "Symbol": name.replace(".BK", ""),
            "Ticker": ticker,
            "Price": price,
            "RSI": rsi,
            "Vol": vol_st, 
            "Strategy": strat,
            "Action": act,
            "P/E": f"{pe:.1f}" if pe > 0 else "-",
            "Div %": f"{div:.2f}%" if div > 0 else "-",
            "Trend": trend,
            "Color": col,
            "TextColor": txt_col
        })
    my_bar.progress((i + 1) / len(all_tickers))
my_bar.empty()

if data_list:
    res_df = pd.DataFrame(data_list)
    cols = ["Symbol", "Price", "RSI", "Vol", "Strategy", "Action", "P/E", "Div %", "Trend"]
    
    def highlight_rows(row):
        bg_color = row.get("Color", "white")
        txt_color = row.get("TextColor", "black")
        return [f'background-color: {bg_color}; color: {txt_color}'] * len(row)

    st.dataframe(res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
                 column_order=cols, height=500, use_container_width=True)

    # --- 6. Deep Dive & Personal Plan ---
    st.write("---")
    
    col_chart, col_decision = st.columns([1.5, 1])
    
    with col_chart:
        st.subheader("🔍 Technical Chart")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้นเพื่อวิเคราะห์:", symbol_list)
        target = next((t for n, t in all_tickers if n.replace(".BK", "") == selected_symbol), None)

        if target:
            df_chart, _, div_yield = get_data_from_yahoo(target)
            if df_chart is not None:
                current_price_default = float(df_chart['Close'].iloc[-1])
                recent_low = df_chart['Low'].tail(20).min()
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                
                # เส้นแนวรับ
                fig.add_hline(y=recent_low, line_dash="dot", line_color="green", annotation_text="Support", row=1, col=1)
                
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

    with col_decision:
        st.subheader("🧠 Personal Advisor (ที่ปรึกษาส่วนตัว)")
        
        st.markdown('<div class="personal-zone">', unsafe_allow_html=True)
        st.markdown(f"#### 💼 สถานะของคุณกับ {selected_symbol}")
        
        # 1. รับข้อมูลต้นทุน
        avg_cost = st.number_input("ต้นทุนเฉลี่ย (บาท)", value=0.0, step=0.1, format="%.2f", key=f"cost_{selected_symbol}")
        qty = st.number_input("จำนวนหุ้นที่มี", value=0, step=100, key=f"qty_{selected_symbol}")
        
        # 2. วิเคราะห์สถานะ
        rsi_val = df_chart['RSI'].iloc[-1]
        
        if qty > 0 and avg_cost > 0:
            market_val = current_price_default * qty
            cost_val = avg_cost * qty
            unrealized = market_val - cost_val
            pct = (unrealized / cost_val) * 100
            
            # โชว์กำไร/ขาดทุน
            if unrealized < 0:
                st.error(f"📉 ขาดทุน: {unrealized:,.0f} ฿ ({pct:.2f}%)")
            else:
                st.success(f"🎉 กำไร: +{unrealized:,.0f} ฿ (+{pct:.2f}%)")

            # 3. คำแนะนำ: ควรซื้อเพิ่มไหม? (Accumulation Logic)
            st.markdown("---")
            st.markdown("#### 🛒 คำแนะนำ: จะซื้อเพิ่มดีไหม?")
            
            rec_action = ""
            rec_detail = ""
            rec_style = ""
            
            # Logic ตัดสินใจ
            is_uptrend = current_price_default > df_chart['EMA200'].iloc[-1]
            
            if rsi_val <= 30:
                rec_action = "🔥 BUY NOW! (จัดหนัก)"
                rec_detail = "ราคาถูกมาก (Oversold) โอกาสเด้งสูง ควรซื้อเพื่อดึงทุนลง"
                rec_style = "buy-box"
            elif rsi_val <= 45:
                if current_price_default < avg_cost:
                    rec_action = "✅ BUY DIP (ซื้อถัว)"
                    rec_detail = f"ราคาต่ำกว่าทุน ({current_price_default:.2f} < {avg_cost:.2f}) และย่อตัวสวย น่าสะสม"
                    rec_style = "buy-box"
                elif is_uptrend:
                    rec_action = "🛒 BUY MORE (ซื้อเพิ่ม)"
                    rec_detail = "ราคาขึ้นแต่ย่อตัว (Buy on Dip) ซื้อเพื่อรันเทรนด์ต่อ"
                    rec_style = "buy-box"
                else:
                    rec_action = "🤔 WAIT (รอก่อน)"
                    rec_detail = "ราคากลางๆ ไม่ถูกไม่แพง รอแนวรับดีกว่า"
                    rec_style = "wait-box"
            elif rsi_val >= 70:
                rec_action = "🛑 STOP BUY (ห้ามซื้อ)"
                rec_detail = "ราคาแพงเกินไป (Overbought) ระวังดอย ควรแบ่งขายทำกำไร"
                rec_style = "wait-box"
            else:
                rec_action = "⏳ WAIT (รอดู)"
                rec_detail = "ไม่มีสัญญาณชัดเจน ถือเงินสดรอ"
                rec_style = "wait-box"

            # แสดงผลคำแนะนำ
            st.markdown(f"""
            <div class="{rec_style}">
                <h3 style="margin:0;">{rec_action}</h3>
                <p style="margin:5px 0 0 0;">{rec_detail}</p>
            </div>
            """, unsafe_allow_html=True)

            # 4. เครื่องคิดเลขต้นทุนใหม่ (Simulator)
            if "BUY" in rec_action:
                st.write("")
                with st.expander("🧮 คำนวณต้นทุนใหม่ (ถ้าซื้อเพิ่ม)", expanded=True):
                    add_shares = st.number_input("จะซื้อเพิ่มกี่หุ้น?", value=int(qty), step=100, key=f"add_{selected_symbol}")
                    if add_shares > 0:
                        new_cost = ((avg_cost * qty) + (current_price_default * add_shares)) / (qty + add_shares)
                        diff = new_cost - avg_cost
                        
                        st.write(f"ซื้อ **{add_shares:,}** หุ้น ที่ราคา **{current_price_default:.2f}**")
                        st.metric("ต้นทุนใหม่ (New Avg)", f"{new_cost:,.2f} บาท", f"{diff:+.2f} บาท", delta_color="inverse")
            
            # 5. คำแนะนำการขาย
            if unrealized > 0:
                 st.write("")
                 st.markdown("#### 💰 วางแผนขายทำกำไร")
                 if div_yield > 4.0:
                     st.info(f"🛡️ **แนะนำถือต่อ:** หุ้นนี้ปันผลดี ({div_yield:.1f}%) เป็น Cash Cow ชั้นดี")
                 elif rsi_val > 70:
                     st.warning("🚨 **แนะนำขาย:** RSI สูง ระวังย่อตัว")
                 else:
                     st.success("💎 **ถือต่อ (Run Trend):** แนวโน้มยังดี")

        else:
            st.info("กรอกต้นทุนเพื่อรับคำแนะนำเฉพาะบุคคล")
            if rsi_val <= 45:
                 st.success(f"✅ ไม้แรกน่าสน! RSI {rsi_val:.0f} (ต่ำ) ราคา {current_price_default:.2f}")
            else:
                 st.warning(f"⚠️ รออีกนิด! RSI {rsi_val:.0f} ยังไม่ถูกพอ รอแถวแนวรับ {recent_low:.2f}")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
