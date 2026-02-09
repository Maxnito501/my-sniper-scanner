import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V5.9", page_icon="💎", layout="wide")

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

st.title("💎 Polaris V5.9: Strategic Advisor (Fixed)")
st.markdown("**ระบบวิเคราะห์จังหวะเข้าทำ: คำนวณราคาที่เหมาะสมสำหรับการ 'ซื้อเพิ่ม' หรือ 'ขายทำกำไร'**")
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
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if len(df) < 100: return None, 0, 0, "N/A"

        # Indicators
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['VolMA'] = df['Volume'].rolling(20).mean()

        # Fundamental & XD
        info = stock.info
        pe = info.get('trailingPE', 0)
        
        raw_div = info.get('dividendYield', 0)
        div_yield = (raw_div * 100) if raw_div and raw_div < 1 else (raw_div if raw_div else 0)
        if div_yield > 20: div_yield = 0 # Filter Error
        
        xd_timestamp = info.get('exDividendDate')
        if xd_timestamp:
            xd_date = datetime.fromtimestamp(xd_timestamp).strftime('%d/%m/%Y')
        else:
            xd_date = "-"

        return df, pe, div_yield, xd_date
    except: return None, 0, 0, "-"

# --- 4. Strategy Engine ---
def analyze_data(df, pe, div):
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

# --- 5. Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]
my_bar = st.progress(0)

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
    my_bar.progress((i + 1) / len(all_tickers))
my_bar.empty()

if data_list:
    res_df = pd.DataFrame(data_list)
    cols = ["Symbol", "Price", "RSI", "Strategy", "Action", "P/E", "Div %", "XD Date"]
    
    # 🛠️ FIX: ฟังก์ชันระบายสีที่ถูกต้อง (ไม่ใช้ subset ใน apply)
    def highlight_rows(row):
        bg_color = row.get("Color", "white")
        txt_color = row.get("TextColor", "black")
        # คืนค่าสีให้ครบทุกคอลัมน์ใน row
        return [f'background-color: {bg_color}; color: {txt_color}'] * len(row)

    # Apply style กับทั้ง DataFrame ก่อน แล้วค่อยเลือกโชว์เฉพาะคอลัมน์ที่ต้องการ
    st.dataframe(
        res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
        column_order=cols, # เลือกคอลัมน์ที่จะโชว์ตรงนี้แทน
        height=500,
        use_container_width=True
    )

    # --- 6. Deep Dive & Personal Advisor ---
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
                recent_low = df_chart['Low'].tail(20).min()
                recent_high = df_chart['High'].tail(20).max()
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                
                fig.add_hline(y=recent_low, line_dash="dot", line_color="green", annotation_text="Support (รอซื้อ)", row=1, col=1)
                fig.add_hline(y=recent_high, line_dash="dot", line_color="red", annotation_text="Resistance (ขายทำกำไร)", row=1, col=1)
                
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

    with col_decision:
        st.subheader("🧠 Personal Advisor (ที่ปรึกษาแก้พอร์ต)")
        
        st.markdown('<div class="personal-zone">', unsafe_allow_html=True)
        st.markdown(f"#### 💼 แผนการเล่น {selected_symbol}")
        
        avg_cost = st.number_input("ต้นทุนเฉลี่ย (บาท)", value=0.0, step=0.1, format="%.2f", key=f"cost_{selected_symbol}")
        qty = st.number_input("จำนวนหุ้นที่มี", value=0, step=100, key=f"qty_{selected_symbol}")
        
        # Pull RSI & Price from chart data
        if target and df_chart is not None:
            rsi_val = df_chart['RSI'].iloc[-1]
        else:
            rsi_val = 50 # Default

        # แสดงสถานะปัจจุบัน
        st.write("---")
        st.markdown(f"**ราคาตลาด:** {current_price_default:,.2f} บาท")
        st.markdown(f"**แนวรับ (Support):** {recent_low:,.2f} บาท")
        st.markdown(f"**แนวต้าน (Resistance):** {recent_high:,.2f} บาท")

        if qty > 0 and avg_cost > 0:
            market_val = current_price_default * qty
            cost_val = avg_cost * qty
            unrealized = market_val - cost_val
            pct = (unrealized / cost_val) * 100
            
            if unrealized < 0:
                st.error(f"📉 ขาดทุน: {unrealized:,.0f} ฿ ({pct:.2f}%)")
                # คำแนะนำเมื่อขาดทุน
                advice_html = ""
                if current_price_default <= recent_low * 1.01: # ใกล้แนวรับ
                    if rsi_val <= 45:
                        advice_html = f"""
                        <div class="buy-zone">
                            <h3>✅ ซื้อถัวได้! (Average Down)</h3>
                            <p>ราคาชนแนวรับ ({recent_low:.2f}) + RSI ต่ำ</p>
                            <p>โอกาสเด้งสูง เหมาะแก่การลดต้นทุน</p>
                        </div>
                        """
                    else:
                        advice_html = f"""
                        <div class="wait-zone">
                            <h3>🤔 รอสัญญาณ (Wait)</h3>
                            <p>ถึงแนวรับแล้ว แต่ RSI ยังไม่ต่ำพอ</p>
                            <p>รอแท่งเทียนกลับตัวก่อน</p>
                        </div>
                        """
                else:
                    advice_html = f"""
                    <div class="hold-zone">
                        <h3>⏳ ถือรอ (Hold)</h3>
                        <p>ราคายังลอยอยู่กลางทาง</p>
                        <p>รอให้ลงมาถึง {recent_low:.2f} ค่อยพิจารณา</p>
                    </div>
                    """
                st.markdown(advice_html, unsafe_allow_html=True)

            else:
                st.success(f"🎉 กำไร: +{unrealized:,.0f} ฿ (+{pct:.2f}%)")
                # คำแนะนำเมื่อกำไร
                if current_price_default >= recent_high * 0.99:
                    st.markdown("""
                    <div class="sell-zone">
                        <h3>💰 พิจารณาขาย (Take Profit)</h3>
                        <p>ราคาชนต้านเดิมแล้ว ระวังย่อตัว</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="hold-zone">
                        <h3>💎 รันเทรนด์ (Run Trend)</h3>
                        <p>แนวโน้มยังไปต่อได้ ถือลุ้น High เดิม</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # เครื่องคิดเลขต้นทุนใหม่
            st.write("---")
            with st.expander("🧮 คำนวณต้นทุนใหม่ (ถ้าซื้อเพิ่ม)", expanded=False):
                add_shares = st.number_input("จะซื้อเพิ่มกี่หุ้น?", value=100, step=100, key=f"add_{selected_symbol}")
                if add_shares > 0:
                    new_cost = ((avg_cost * qty) + (current_price_default * add_shares)) / (qty + add_shares)
                    diff_cost = avg_cost - new_cost
                    st.info(f"👉 ต้นทุนใหม่จะลดลงเหลือ: **{new_cost:.2f} บาท** (ลดลง {diff_cost:.2f} บาท)")

        else:
            st.info("กรอกต้นทุนเพื่อรับคำแนะนำ")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
