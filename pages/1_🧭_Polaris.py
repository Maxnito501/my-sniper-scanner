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
    .avg-calculator { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px dashed #9ca3af; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V6.0: Portfolio Doctor (Fixed)")
st.markdown("**หมอประจำพอร์ต: วิเคราะห์จังหวะ ถัว/ถือ/เท (รายตัว)**")
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
all_tickers = STOCKS + list(FUNDS.keys())
my_bar = st.progress(0)

for i, ticker in enumerate(all_tickers):
    df, pe, div, xd = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, strat, act, col, txt_col = analyze_data(df, pe, div)
        name_show = ticker.replace(".BK", "")
        
        data_list.append({
            "Symbol": name_show, "Ticker": ticker, "Price": price, "RSI": rsi,
            "Strategy": strat, "Action": act, "P/E": f"{pe:.1f}" if pe else "-",
            "Div %": f"{div:.2f}%" if div else "-", "XD Date": xd,
            "Trend": trend, "Color": col, "TextColor": txt_col
        })
    my_bar.progress((i + 1) / len(all_tickers))
my_bar.empty()

if data_list:
    res_df = pd.DataFrame(data_list)
    cols = ["Symbol", "Price", "RSI", "Strategy", "Action", "P/E", "Div %", "XD Date"]
    
    # 🛠️ FIX: ลบ subset ออก เพื่อให้เห็นคอลัมน์ Color
    def highlight_rows(row):
        return [f'background-color: {row["Color"]}; color: {row["TextColor"]}'] * len(row)

    # 🛠️ FIX: ย้ายการเลือกคอลัมน์มาไว้ที่ column_order แทน
    st.dataframe(
        res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
        column_order=cols, 
        height=500, 
        use_container_width=True
    )

    # --- 6. Deep Dive & Personal Advisor ---
    st.write("---")
    col_chart, col_doctor = st.columns([1.5, 1])
    
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

    with col_doctor:
        st.subheader("👨‍⚕️ Portfolio Doctor")
        
        st.markdown('<div class="personal-zone">', unsafe_allow_html=True)
        st.markdown(f"#### 💼 แผนการเล่น {selected_symbol}")
        
        avg_cost = st.number_input("ต้นทุนเฉลี่ย", value=0.0, step=0.1, format="%.2f", key=f"cost_{selected_symbol}")
        qty = st.number_input("จำนวนหุ้น", value=0, step=100, key=f"qty_{selected_symbol}")
        
        stock_type = STOCK_DNA.get(ticker, "Growth")
        
        if qty > 0 and avg_cost > 0:
            market_val = curr_price * qty
            cost_val = avg_cost * qty
            unrealized = market_val - cost_val
            pct = (unrealized / cost_val) * 100
            
            if unrealized < 0:
                st.error(f"📉 ขาดทุน: {unrealized:,.0f} ฿ ({pct:.2f}%)")
                
                if curr_price <= recent_low * 1.015:
                    st.markdown(f"""
                    <div class="buy-zone">
                        <h3>💉 จ่ายยา: ซื้อถัว (Average Down)</h3>
                        <p>ราคาลงมาที่แนวรับสำคัญ ({recent_low:.2f})</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="avg-calculator">', unsafe_allow_html=True)
                    st.markdown("**🧮 เครื่องคำนวณต้นทุนใหม่**")
                    add_amt = st.number_input("จะซื้อเพิ่มกี่บาท?", value=5000, step=1000, key="calc_amt")
                    if add_amt > 0:
                        add_shares = int(add_amt / curr_price)
                        new_avg = ((avg_cost * qty) + (curr_price * add_shares)) / (qty + add_shares)
                        diff = avg_cost - new_avg
                        st.info(f"👉 ได้หุ้นเพิ่ม: **{add_shares}** หุ้น")
                        st.success(f"📉 ต้นทุนลดลงเหลือ: **{new_avg:.2f}** (ลดไป {diff:.2f} บาท)")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                else:
                    st.markdown(f"""
                    <div class="wait-zone">
                        <h3>🛌 จ่ายยา: นอนพัก (Wait)</h3>
                        <p>ราคายังลอยอยู่ (แนวรับถัดไป {recent_low:.2f})</p>
                    </div>
                    """, unsafe_allow_html=True)

            else:
                st.success(f"🎉 สถานะ: กำไร {unrealized:,.0f} ฿ (+{pct:.2f}%)")
                if stock_type == "Dividend":
                    st.markdown("""
                    <div class="hold-zone">
                        <h3>🛡️ คำแนะนำ: ถือต่อ (Hold for Yield)</h3>
                        <p>หุ้นปันผลเน้นถือยาว เก็บกินดอกเบี้ย ไม่ต้องรีบขาย</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    if curr_price >= recent_high * 0.98:
                        st.markdown(f"""
                        <div class="sell-zone">
                            <h3>💰 คำแนะนำ: ขายทำกำไร (Take Profit)</h3>
                            <p>ราคาชนแนวต้าน ({recent_high:.2f})</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="hold-zone">
                            <h3>🚀 คำแนะนำ: รันเทรนด์ (Let Profit Run)</h3>
                            <p>ราคายังไปต่อได้</p>
                        </div>
                        """, unsafe_allow_html=True)

        else:
            st.info("กรอกต้นทุนเพื่อเริ่มวินิจฉัยพอร์ต")
            st.markdown(f"**นิสัยหุ้นตัวนี้:** {stock_type}")
            
            if curr_price <= recent_low * 1.02:
                st.success(f"✅ น่าซื้อ: ราคาใกล้แนวรับ {recent_low:.2f}")
            else:
                st.warning(f"⏳ รอซื้อ: แนวรับถัดไป {recent_low:.2f} (ตอนนี้แพงไป)")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
